# Nuclear cleanup - removes EVERYTHING
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm -f $(docker ps -aq) 2>/dev/null || true
docker network prune -f
docker volume prune -f
docker system prune -a --volumes -f

# Remove old project files
rm -rf ~/curavani_backend/*
rm -rf ~/curavani_frontend_internal/*
rm -rf ~/Recovery_Test/*