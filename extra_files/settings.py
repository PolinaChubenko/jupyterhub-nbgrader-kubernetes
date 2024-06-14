import os

c.MappingKernelManager.cull_connected = False
c.MappingKernelManager.cull_busy = False
c.MappingKernelManager.cull_idle_timeout = 259200
c.NotebookApp.shutdown_no_activity_timeout = 259200

c.KubeSpawner.auth_state_hook = userdata_hook
c.KubeSpawner.pre_spawn_hook = bootstrap_pre_spawn
c.KubeSpawner.automount_service_account_token = False