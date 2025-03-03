import install_docker
import docker_start

def main():
    install_docker.begin()
    docker_start.begin()

if __name__ == "__main__":
    main()