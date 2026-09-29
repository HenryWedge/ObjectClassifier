minikube ssh -- "sudo sysctl -w fs.inotify.max_user_instances=1024 fs.inotify.max_user_watches=524288 fs.inotify.max_queued_events=32768"
