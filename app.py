import modal, os,

app = modal.App("All-In-One-FaceFusion")
vol = modal.Volume.from_name("workspace", create_if_missing=True)

# ============ Installing FaceFusion ============
def install_facefusion():
    # 1. Clone FaceFusion
    print("Installing FaceFusion...⬇️")
    os.system("cd /root/workspace && git clone https://github.com/facefusion/facefusion.git")

    # 2. Run FaceFusion's official installation script
    print("Running FaceFusion installation script...⬇️")
    os.system("bash -c 'source /opt/conda/bin/activate && cd /root/workspace/facefusion && python install.py --onnxruntime cuda'")
    
    print("FaceFusion Installed...✅")
# ============ FaceFusion Download Finished ============

# ============ Installing Jupyterlabs ============
def Install_code_server():
    print("Installing code server...⬇️")
    # Configure JupyterLab
    os.system("mkdir -p /root/.jupyter/lab/user-settings/@jupyterlab/apputils-extension")
    os.system('echo \'{"theme": "JupyterLab Dark"}\' > /root/.jupyter/lab/user-settings/@jupyterlab/apputils-extension/themes.jupyterlab-settings')

    #Cloudflared Installation
    os.system("wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O cloudflared && chmod +x cloudflared && mv cloudflared /usr/local/bin/")
    
    # Recreate banner
    os.system("""cat > /root/.bash_motd << 'EOF'
___________                  ___________           .__               
\_   _____/____    ____  ____\_   _____/_ __  _____|__| ____   ____  
 |    __) \__  \ _/ ___\/ __ \|    __)|  |  \/  ___/  |/  _ \ /    \ 
 |     \   / __ \\  \__\  ___/|     \ |  |  /\___ \|  (  <_> )   |  \
 \___  /  (____  /\___  >___  >___  / |____//____  >__|\____/|___|  /
     \/        \/     \/    \/    \/             \/               \/ 

EOF""")

    # Recreate bashrc
    os.system("""cat > /root/.bashrc << 'EOF'
cat /root/.bash_motd 2>/dev/null
cd /root/workspace
EOF""")

    # Recreate profile
    os.system("""cat > /root/.profile << 'EOF'
[ -n "$PS1" ] && exec bash
EOF""")
# ============ Jupyterlabs Download Finished ============


images = (
    modal.Image.debian_slim(python_version="3.12")  # Changed from 3.11 to 3.12
    
    # LAYER#2 INSTALL SYSTEM DEPENDENCIES
    .apt_install("ffmpeg", "curl", "git-all", "wget")
    
    # LAYER#3 INSTALL MINICONDA
    .run_commands(
        "curl -LO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh",
        "bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda",
        "rm Miniconda3-latest-Linux-x86_64.sh",
        "/opt/conda/bin/conda init bash",
    )
    .env({"PATH": "/opt/conda/bin:$PATH"})
    
    # LAYER#4 CONFIGURE CONDA
    .run_commands(
        "/opt/conda/bin/conda config --set allow_conda_downgrades true",
        "/opt/conda/bin/conda config --set channel_priority flexible",
        "/opt/conda/bin/conda config --add channels conda-forge",
        "/opt/conda/bin/conda config --remove channels defaults || true",
    )
    
    # LAYER#5 INSTALL CUDA RUNTIME & CUDNN via Conda
    .run_commands(
        "/opt/conda/bin/conda install -y --override-channels -c nvidia/label/cuda-12.9.1 -c nvidia/label/cudnn-9.10.0 -c conda-forge cuda-runtime cudnn",
    )
    
    # LAYER#6 INSTALL PYTHON PACKAGES
    .pip_install("jupyterlab","notebook","ipykernel","gdown","opencv-python","onnxruntime-gpu",)
    
    # LAYER#8 CONFIGURE JUPYTERLAB
    .run_function( 
        Install_code_server,
    )
    
    # LAYER#9 INSTALL FACEFUSION
    .run_function(
        install_facefusion,
        volumes={"/root/workspace": vol},
    )
    
    # NOTE: ADD NEW FUNCTION HERE (LAST LAYER) SO THE IMAGE WOULDN'T REBUILD FROM FIRST
)

@app.function(
    image=images,
    timeout=24*3600, 
    gpu="L40S",
    volumes={"/root/workspace": vol},
)
def run():
    # ===================== CLOUDFLARED TUNNEL ======================
    os.system("jupyter lab --ip=0.0.0.0 --port=5000 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password='' &")
    # os.system("cd /root/workspace/facefusion && python facefusion.py run &")
    os.system("cloudflared tunnel --url http://localhost:5000 & cloudflared tunnel --url http://localhost:7860")
    # ===================== CLOUDFLARED TUNNEL ======================
