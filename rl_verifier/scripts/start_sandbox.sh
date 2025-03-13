docker run -d  \
    --privileged \
    -p 8080:8080 \
    -e WORKER_SIZE=8 \
    tuenguyen/code_sandbox:server \
    make run-online