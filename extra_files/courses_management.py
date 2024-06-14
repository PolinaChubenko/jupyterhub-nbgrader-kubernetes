from traitlets import default, Unicode
from tornado import gen
import os
import json
from kubespawner import KubeSpawner
import asyncio
import kubernetes_asyncio
from kubernetes_asyncio import config, client
from kubernetes_asyncio.client import (
    V1ObjectMeta,
    V1Secret,
    V1PersistentVolume,
    V1PersistentVolumeClaim,
    V1ResourceRequirements,
    V1LabelSelector,
    V1CSIPersistentVolumeSource,
    V1PersistentVolumeSpec,
    V1PersistentVolumeClaimSpec,
    ApiException,
)

PVC_STORAGE_CLASS = "standard"

# Define all the courses and their instructors
with open('/usr/local/etc/jupyterhub/jupyterhub_config.d/courses_info.json') as file:
    COURSES = json.load(file)

def userdata_hook(spawner, auth_state):
    spawner.userdata = auth_state

async def check_pvc(home_pvc_name, namespace):
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        v1 = kubernetes_asyncio.client.CoreV1Api(api_client)
        pvcs = await v1.list_namespaced_persistent_volume_claim(namespace)
        for claim in pvcs.items:
            if claim.metadata.name == home_pvc_name:
                return claim
        return None

async def delete_pvc(namespace, pvc):
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        v1 = kubernetes_asyncio.client.CoreV1Api(api_client)
        await v1.delete_namespaced_persistent_volume_claim(name=pvc, namespace=namespace)
        await asyncio.sleep(1)

async def create_pvc(home_pvc_name, home_pv_name, namespace, storage_class, capacity):
    pvc = V1PersistentVolumeClaim()
    pvc.api_version = "v1"
    pvc.kind = "PersistentVolumeClaim"
    pvc.metadata = V1ObjectMeta()
    pvc.metadata.name = home_pvc_name
    pvc.spec = V1PersistentVolumeClaimSpec()
    pvc.spec.access_modes = ['ReadWriteMany']
    pvc.spec.resources = V1ResourceRequirements()
    pvc.spec.resources.requests = {"storage": capacity}
    pvc.spec.storage_class_name = storage_class
    if storage_class != PVC_STORAGE_CLASS:
        pvc.spec.selector = V1LabelSelector()
        pvc.spec.selector.match_labels = {"name": home_pv_name}
    try:
        async with kubernetes_asyncio.client.ApiClient() as api_client:
            v1 = kubernetes_asyncio.client.CoreV1Api(api_client)
            x = await v1.create_namespaced_persistent_volume_claim(namespace, pvc)
            await asyncio.sleep(1)
    except ApiException as e:
        if re.search("object is being deleted:", e.body):
            raise web.HTTPError(401, "Can't delete PVC {}, please contact administrator!".format(home_pvc_name))
            return False
    return True

def add_volume(spawner_vol_list, volume, volname):
    if len(spawner_vol_list) == 0:
        spawner_vol_list = [volume]
    else:
        volume_exists = False
        for vol in spawner_vol_list:
            if "name" in vol and vol["name"] == volname:
                volume_exists = True
        if not volume_exists:
            spawner_vol_list.append(volume)

def mount(spawner, pv, pvc, mountpath, type):
    volume = {}
    volume_mount = {}
    if type == "pvc":
        volume = {"name": pv, "persistentVolumeClaim": {"claimName": pvc}}
        volume_mount = {"mountPath": mountpath, "name": pv}
    elif type == "cm":
        volume = {"name": pv, "configMap": {"name": pvc}}
        volume_mount = {"mountPath": mountpath, "name": pv}
    add_volume(spawner.volumes, volume, pv)
    add_volume(spawner.volume_mounts, volume_mount, pvc)

async def mount_persistent_hub_home(spawner, username, namespace):
    hub_home_name = username + "-home-default"

    pvc = await check_pvc(hub_home_name, namespace)
    if not pvc:
        await create_pvc(hub_home_name, hub_home_name + "-pv", namespace, PVC_STORAGE_CLASS, "10Gi")

    mount(spawner, hub_home_name + "-pv", hub_home_name, "/home/jovyan", "pvc")

def set_resources(spawner):
    spawner.container_security_context = {"capabilities": {"drop": ["ALL"]}}

async def bootstrap_pre_spawn(spawner):
    config.load_incluster_config()
    groups = []
    for n in spawner.user.groups:
        groups.append(n.name)
    namespace = spawner.namespace
    username = spawner.user.name
    spawner.user.name = spawner.user.name.replace('.', '-')

    spawner.start_timeout = 600

    await mount_persistent_hub_home(spawner, spawner.user.name, namespace)

    isStudent = True
    volume = {"name": "nbgrader-exchange", "persistentVolumeClaim": {"claimName": "nbgrader-exchange"}}
    add_volume(spawner.volumes, volume, volume["name"])

    for group in groups:
        if group.startswith("formgrade-"):
            isStudent = False
            courseName = group.replace("formgrade-", "")

            volume_mount = {"mountPath": f"/mnt/exchange", "name": "nbgrader-exchange"}
            add_volume(spawner.volume_mounts, volume_mount, volume_mount["name"])
        elif group.startswith("nbgrader-"):
            courseName = group.replace("nbgrader-", "")

            if not os.path.exists(f'/mnt/exchange/{courseName}/inbound/{username}'):
                os.makedirs(f"/mnt/exchange/{courseName}/inbound/{username}")
            if not os.path.exists(f'/mnt/exchange/{courseName}/feedback_public/{username}'):
                os.makedirs(f"/mnt/exchange/{courseName}/feedback_public/{username}")

            spawner.volume_mounts.extend([
                {
                    "name": "nbgrader-exchange", 
                    "mountPath": f"/mnt/exchange/{courseName}/inbound/{username}",
                    "subPath": f"{courseName}/inbound/{username}",
                },
                {
                    "name": "nbgrader-exchange", 
                    "mountPath": f"/mnt/exchange/{courseName}/feedback_public/{username}",
                    "subPath": f"{courseName}/feedback_public/{username}",
                },
                {
                    "name": "nbgrader-exchange",
                    "mountPath": f"/mnt/exchange/{courseName}/outbound",
                    "subPath": f"{courseName}/outbound",
                    "readOnly": True
                }
            ])
    
    if isStudent:
        spawner.image = "nbgrader-student-sample:0.0.1"
    else:
        spawner.image = "nbgrader-instructor-sample:0.0.1"

    set_resources(spawner)

    if "--SingleUserNotebookApp.max_body_size=6291456000" not in spawner.args:
        spawner.args.append("--SingleUserNotebookApp.max_body_size=6291456000")


groupsToCreate = {}

base_port = 9000
idx = 0
for course, instructors in COURSES.items():
    # "outbound" must exist before starting a singleuser 
    if not os.path.exists(f'/mnt/exchange/{course}/outbound'):
        os.makedirs(f"/mnt/exchange/{course}/outbound")
    if not os.path.exists(f'/mnt/exchange/{course}/inbound'):
        os.makedirs(f"/mnt/exchange/{course}/inbound")
    if not os.path.exists(f'/mnt/exchange/{course}/feedback_public'):
        os.makedirs(f"/mnt/exchange/{course}/feedback_public")
  
    with open(f"/mnt/exchange/{course}/nbgrader_config.py", "w") as f:
        f.write("c = get_config()\n")
        f.write(f"c.CourseDirectory.root = '/mnt/exchange/{course}'\n")
        f.write(f"c.CourseDirectory.course_id = '{course}'\n")

    c.JupyterHub.services.append(
        {
            "name": course,
            "url": f"http://course-svc:{base_port + idx}",
            "command": ["jupyterhub-singleuser", f"--group=formgrade-{course}", f"--port={base_port + idx}", "--debug", "--ServerApp.ip=0.0.0.0"],
            "cwd": f"/mnt/exchange/{course}",
            "oauth_no_confirm": True,
            "environment" : {
                # Here nbgrader.auth.JupyterHubAuthPlugin needs a user, that always exists
                "JUPYTERHUB_USER": "admin"
            }
        }
    )

    groupsToCreate[f"nbgrader-{course}"] = [] # students are added here
    groupsToCreate[f"formgrade-{course}"] = instructors

    c.JupyterHub.load_roles.append({
        "name": f"formgrade-{course}",
        "groups": [f"formgrade-{course}"],
        "services": [course],
        "scopes": [
        f"access:services!service={course}", 
        f"read:services!service={course}", 
        f"list:services!service={course}", 
        "groups", 
        "users"
        ]
    })
    idx += 1

c.JupyterHub.load_roles.append({"name": "server", "scopes": ["inherit"]})  # for course_list to work 
c.JupyterHub.load_groups = groupsToCreate

# adding token for manager
token = os.getenv("MANAGER_TOKEN")
c.JupyterHub.api_tokens = {
    token: 'admin',
}
