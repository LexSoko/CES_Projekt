# VS Code
for black formatter settings [visit me](https://marcobelo.medium.com/setting-up-python-black-on-visual-studio-code-5318eba4cd00)\
for pylint linting settings [visit me](https://code.visualstudio.com/docs/python/linting)\
for anaconda environment settings [visit me](https://code.visualstudio.com/docs/python/environments)\
for pytesting [visit me](https://code.visualstudio.com/docs/python/testing)

# SSH
[link to ssh guide](https://stackoverflow.com/questions/30202642/how-can-i-clone-a-private-gitlab-repository/50079018#50079018)

keep in mind, that for this project you have to use `gitlab.tugraz.at` instead of `gitlab.com`.

Also following command may get you a timeout error, in this case proceed to git cloning\
```console
> ssh -i $PWD/.ssh/id_rsa git@gitlab.tugraz.at
```

PS.: `$PWD` stands for your local user directory


# Git
clone the project:
```console
> git clone https://gitlab.tugraz.at/<your_gitlab_username>/<gitlab_project_name>.git
```

## submodule commands
add a submodule:
```console
> git submodule add <Repository HTTPS URL>
```

initialize submodule configuration files
```console
> git submodule init
```

fetch all the data from submodule project
```console
> git submodule update
```

combine init and update in 1 command
```console
> git submodule update --init
```

# Anaconda3 useage
make sure you added following paths to your System PATH:
```{Anaconda_Install_Dir}\Anaconda3\pkgs\```
```{Anaconda_Install_Dir}\Anaconda3\Scripts```
```{Anaconda_Install_Dir}\Anaconda3\Library\bin```

when using the `conda` command in any terminal (cmd.exe, powershell, bash) make sure you first initialised conda for the specific shell with following command(conda will ask you to do that, when you try to do any conda commands):
```console
> conda init <shell_name>
```

## Create and activate new anaconda environment with Python 3.8
first go to cmd and type following:
```console
> conda create --name ces-mma python=3.8
```
then to activate this environment, use
```console
> conda activate ces-mma
```
install package
```console
> conda install <package_name>
```
install package with specific version
```console
> conda install <package_name>=<version_number>
```
install package with specific version from specific channel (some packages are not available under default channel but have to be installed from conda-forge channel)
```console
> conda install <package_name>
```

export conda environment
```console
> conda env export > environment.yml
```
import conda env from .yml file
```console
> conda env create -f environment.yml
```
verify with 
```console
> conda env list
```
update conda environment from environment.yml
```console
> conda env update --name ces-mma --file environment.yml --prune
```

# profiling with snakeviz
run cprofile
```console
> python -m cProfile -o <script_name>.prof <assignment_folder>/<script_name>.py
```
run snakeviz
```console
>  snakeviz <script_name>.prof
```

# textual setup
1. conda environment updaten
2. in einem terminal development console starten:
```console
> textual console
```
2. in einem zweiten terminal unsere app im dev mode starten:
```console
> textual run --dev .\code_python\enceladus\winder_enceladus_interface.py
`````