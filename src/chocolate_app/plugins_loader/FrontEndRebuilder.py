from genericpath import isdir
import pathlib
import os
import hashlib
import subprocess
import re
import shutil

from chocolate_app.plugins_loader import loader
from chocolate_app import ChocolateException


def rebuild_frontend():
    """
    Rebuild the frontend

    This function rebuild the frontend, based on the plugins that are installed

    Returns:
        None
    """
    from chocolate_app import config, write_config

    if "PLUGINS" not in config:
        config["PLUGINS"] = {}

    if "plugin_hashs" not in config["PLUGINS"]:
        config["PLUGINS"]["plugin_hashs"] = ""

    plugin_hashs = config["PLUGINS"]["plugin_hashs"]
    new_plugin_hashs = set()

    for plugin_frontend in loader.PLUGIN_FRONTENDS:
        plugin_hash = generate_hash(plugin_frontend)
        new_plugin_hashs.add(plugin_hash)

    plugin_hashs = set(plugin_hashs.split(","))

    if plugin_hashs == new_plugin_hashs:
        return

    new_plugin_hashs = ",".join(new_plugin_hashs)
    config["PLUGINS"]["plugin_hashs"] = new_plugin_hashs

    dir_path = pathlib.Path(__package__).parent.absolute()
    frontend_path = f"{dir_path}/frontend_temp"
    git_clone_command = (
        "git clone https://github.com/ChocolateApp/ChocolateReact.git frontend_temp"
    )

    if os.path.exists(frontend_path):
        shutil.rmtree(frontend_path, ignore_errors=True)
        pass

    subprocess.run(
        git_clone_command.split(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    frontends = loader.PLUGIN_FRONTENDS
    requirements = []
    for plugin_frontend in frontends:
        plugin_hash = generate_hash(plugin_frontend)
        requirements.extend(
            handle_frontend(plugin_frontend, frontend_path, plugin_hash)
        )

    remove_build_files(dir_path)
    build_frontend(frontend_path, dir_path, requirements)
    # delete_frontend_temp(frontend_path)
    write_config(config)


def generate_hash(plugin_frontend: str) -> str:
    """
    Generate a hash for the plugin frontend

    Parameters:
        plugin_frontend (str): The path of the plugin frontend

    Returns:
        str: The hash of the plugin frontend
    """
    hash_md5 = hashlib.md5()
    for folder, subfolders, files in os.walk(plugin_frontend):
        for file in files:
            with open(os.path.join(folder, file), "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
                    hash_md5.update(file.encode())
    return hash_md5.hexdigest()


def delete_frontend_temp(frontend_path: str):
    """
    Delete the frontend temp folder

    Parameters:
        frontend_path (str): The path of the frontend

    Returns:
        None
    """
    shutil.rmtree(frontend_path, ignore_errors=True)


def remove_build_files(chocolate_path: str):
    template_path = f"{chocolate_path}/templates"
    static_path = f"{chocolate_path}/static"
    folders_to_remove = ["js", "css", "media"]
    for folder in folders_to_remove:
        folder_path = f"{static_path}/{folder}"
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path, ignore_errors=True)

    if os.path.exists(f"{template_path}/index.html"):
        os.remove(f"{template_path}/index.html")


def build_frontend(frontend_path: str, chocolate_path: str, requirements: list):
    npm_install_command = "npm install"
    npm_build_command = "npm run build"

    os.chdir(frontend_path)

    subprocess.run(
        npm_install_command.split(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for requirement in requirements:
        subprocess.run(
            f"npm install {requirement}".split(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    subprocess.run(npm_build_command.split(), stdout=subprocess.DEVNULL)

    build_folder = f"{frontend_path}/build"

    if not os.path.exists(f"{build_folder}/static"):
        raise ChocolateException(
            "The build folder does not contain a static folder. You should check the error message above"
        )
    # tout les dossiers dans build_folder/static sont copiés dans chocolate_path/static
    for folder in os.listdir(f"{build_folder}/static"):
        if os.path.isdir(f"{build_folder}/static/{folder}"):
            shutil.copytree(
                f"{build_folder}/static/{folder}",
                f"{chocolate_path}/static/{folder}",
                dirs_exist_ok=True,
            )

    # le fichier index.html est copié dans chocolate_path/templates
    shutil.copy(f"{build_folder}/index.html", f"{chocolate_path}/templates/index.html")


def handle_frontend(plugin_frontend: str, frontend_path: str, plugin_hash: str) -> list:
    """
    Handle the frontend of the plugin

    Parameters:
        plugin_frontend (str): The path of the plugin frontend
        frontend_path (str): The path of the frontend
        plugin_hash (str): The hash of the plugin frontend

    Returns:
        requirements (list): The list of required libraries
    """

    frontend_dirs = ["New", "Append", "Replace"]
    requirements = []
    for frontend_dir in frontend_dirs:
        if os.path.exists(f"{plugin_frontend}/{frontend_dir}"):
            if frontend_dir == "New":
                rqrs = handle_new(
                    f"{plugin_frontend}/{frontend_dir}", frontend_path, plugin_hash
                )
                requirements.extend(rqrs)
    return requirements


def handle_new(new_folder: str, frontend_path: str, plugin_hash: str):
    """
    Handle the new folder

    Parameters:
        new_folder (str): The path of the new folder
        frontend_path (str): The path of the frontend
        plugin_hash (str): The hash of the plugin frontend

    Returns:
        list: The list of required libraries
    """
    required_libs: list[str] = []

    for files in os.listdir(new_folder):
        file_path = f"{new_folder}/{files}"
        if os.path.isfile(file_path):
            url_path = file_path.split("/")[-1]
            url_path = url_path.replace("<", ":").replace(">", "")
            url_path = url_path.replace("\\", "/")
            url_path = url_path.split(".")[0]
            param_args = []

            for match in re.finditer(r"<(.*?)>", file_path):
                param_args.append(match.group(1))

            file_name = ""
            login_required = False
            with open(file_path, "r") as f:
                contenu = f.read()

            description_match = re.search(r"/\*(.*?)\*/", contenu, re.DOTALL)
            description = (
                description_match.group(1).strip() if description_match else None
            )

            if not description:
                raise ChocolateException("Description not found in the file")
            description_lines = description.split("\n")
            description_lines = description_lines[1:]
            while description_lines[-1] == "":
                description_lines.pop()
            while description_lines[0] == "":
                description_lines.pop(0)

            for line in description_lines:
                clean_line = line.strip().rstrip().lower()
                if clean_line.startswith("filename"):
                    file_name = line.split(":")[1].strip()
                    file_name = file_name.replace(" ", "")
                if clean_line.startswith("login"):
                    login_required = clean_line.lower().split(":")[1].strip() == "true"
                if clean_line.startswith("requirements"):
                    required_libs.extend(clean_line.split(":")[1].strip().split(","))

            if not file_name:
                raise ChocolateException("Filename not found in the file")

            file_name = f"{file_name.split('.')[0]}_{plugin_hash}.jsx"

            new_file_code = f"{contenu}"
            new_file_code = re.sub(
                r"export default function (.*?)\(",
                f"export default function \\1_{plugin_hash}(",
                new_file_code,
            )

            import_string = f"import {file_name.replace('.jsx', '')} from './Pages/{file_name.replace('.jsx', '')}'"
            route_string = f"          <Route path=\"/{url_path}\" element={{<{file_name.replace('.jsx', '')}/>}}"
            if not login_required:
                route_string = f"{route_string} no_login={{true}}"
            route_string = f"{route_string} />"

            app_file = f"{frontend_path}/src/App.js"
            new_app_file = ""
            with open(app_file, "r") as f:
                lines = f.readlines()
                last_import_index = next(
                    (
                        i
                        for i, line in enumerate(lines)
                        if not line.startswith("import ")
                    ),
                    len(lines),
                )
                lines.insert(last_import_index, import_string + "\n")

                routes_end_index = next(
                    (i for i, line in enumerate(lines) if line.strip() == "</Routes>"),
                    len(lines),
                )

                lines.insert(routes_end_index, route_string + "\n")

                new_app_file = "".join(lines)

            with open(app_file, "w") as f:
                f.write(new_app_file)
                pass

            create_jsx_file(f"{frontend_path}/src/Pages/{file_name}", new_file_code)

    return required_libs


def create_jsx_file(path: str, content: str) -> None:
    """
    Create a JSX file

    Parameters:
        path (str): The path of the JSX file
        content (str): The content of the JSX file

    Returns:
        None
    """
    with open(path, "w") as file:
        file.write(content)
