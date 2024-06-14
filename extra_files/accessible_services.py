from jupyterhub.handlers import BaseHandler

# In the /hub/home "Services" dropdown, show only courses that the user is enrolled in
def get_accessible_services(self, user):
    accessible_services = []
    if user is None:
        return accessible_services

    courses = []
    for group in user.groups:
        if group.name.startswith("formgrade-"):
            courses.append(group.name.replace("formgrade-", ""))

    for service in self.services.values():
        if not service.name in courses:
            continue
        if not service.url:
            continue
        if not service.display:
            continue
        accessible_services.append(service)

    return accessible_services

BaseHandler.get_accessible_services = get_accessible_services