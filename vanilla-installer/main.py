"""
Most important functions of VanillaInstaller.
"""
# IMPORTS

# Standard library
import os
import sys
import logging
import logging.handlers  # pylance moment
import re
import subprocess
import tempfile
import pathlib
import base64

# External
import requests
import minecraft_launcher_lib as mll
import click


# LOCAL
import theme

PATH_FILE = str(pathlib.Path("data/mc-path.txt").resolve())
FOLDER_LOC = ""


def set_dir(path: str) -> str | None:
    """Sets the Minecraft game directory.

    Args:
        path (str): The path to the Minecraft game directory.
    """
    if path:  # only strings can be written
        path_nobackslash = str(rf"{path}".replace("\\", "/"))
        path_nobackslash = str(rf"{path_nobackslash}".replace(".minecraft", ""))
    else:
        logging.critical("path must be passed!")
        return Exception
    # If the path is none, it will cause the script to fail.
    # In that case, return the default directory.
    if path_nobackslash is not None:
        with open(PATH_FILE, "w", encoding="utf-8") as file:
            file.write(path_nobackslash)
        return path_nobackslash
    if path_nobackslash != "":
        with open(PATH_FILE, "w", encoding="utf-8") as file:
            file.write(path_nobackslash)
        return path_nobackslash
    path_nobackslash_minecraft = mll.utils.get_minecraft_directory()
    path_nobackslash = path_nobackslash_minecraft.replace(".minecraft", "")
    with open(PATH_FILE, "w", encoding="utf-8") as file:
        file.write(path_nobackslash)
    return path_nobackslash


def get_dir() -> str:
    """Returns the Minecraft game directory.

    Returns:
        str: Path
    """
    try:
        path = open(PATH_FILE, encoding="utf-8").read()
    except OSError:
        logging.exception("No mc_path.txt found. Calling set_dir.")
        default_dir = str(
            mll.utils.get_minecraft_directory()
        )  # Without this, it gives an error every time
        path = set_dir(default_dir)
    return path


def newest_version() -> str:
    """Returns the latest version of Minecraft.

    Returns:
      str: The latest Minecraft version
    """
    return mll.utils.get_latest_version()["release"]


def get_java() -> str:
    """Returns the path to a Java executable.

    Returns:
      str: The path to the Java executable
    """
    return mll.utils.get_java_executable()


def fo_to_base64(png_dir: str) -> str:
    """Converts the Fabulously Optimized logo from PNG format into base64.
    The directory specified in `dir` will be searched. If that fails, FO logo will be downloaded over the network.
    Args:
        dir (str): The directory to search for the logo.
    Returns:
        str: The base64 string for the FO logo.
    """

    dir_path = pathlib.Path(png_dir)
    png_content = bytes()

    if (png_path := dir_path / "fo.png").exists():
        png_content = png_path.read_bytes()
    else:
        logging.warning("Cannot find logo locally. Trying to download...")
        url = "https://avatars.githubusercontent.com/u/92206402"
        if (response := requests.get(url)).status_code == 200:
            png_content = response.content
        else:
            logging.critical("Could not get the FO logo over the network.")

    b64logo = base64.b64encode(png_content)
    return str(b64logo)

def get_version():
    version = "v1.0.0-unstable"
    return version

def init() -> None:
    """Initialization for VanillaInstaller."""
    # SET INSTALLATION PATH
    if not os.path.exists(PATH_FILE):
        try:
            path = mll.utils.get_minecraft_directory().replace(".minecraft", "")
            set_dir(path)
        except Exception as error_code:  # any error could happen, really.
            logging.error(
                f"Could not get Minecraft path: {error_code}\nUsing default path based on OS."
            )
            # The first two `startswith` are simply a precaution, since Python previously used a different number for different Linux kernels.
            # The `startswith` for Windows is if they ever change it to `win64` or something, but I doubt that.
            # See https://docs.python.org/3.10/library/sys.html#sys.platform for more.
            if sys.platform.startswith("win"):
                path = os.path.expanduser("~/AppData/Roaming")
                set_dir(path)
            elif sys.platform.startswith("darwin"):
                path = os.path.expanduser("~/Library/Application Support")
                set_dir(path)
            elif sys.platform.startswith("linux"):
                path = os.path.expanduser("~")
                set_dir(path)
            else:
                logging.error("Could not detect OS.")


def text_update(
    text: str, widget=None, mode: str = "info", interface: str = "GUI"
) -> None:
    """Updates the text shown on the GUI window or echoes using Click.

    Args:
        text (str): The text to display
        widget (optional): The widget. Defaults to None.
        mode (str, optional): The type of message to log. Defaults to "info".
        interface (str, optional): The interface to display to. Defaults to "GUI", possible values are "GUI" and "CLI".
    """
    if interface != "CLI":

        if widget:
            widget.master.title(f"{text} » VanillaInstaller")
            widget["text"] = text
            widget["fg"] = theme.load()[mode]

        else:
            if mode == "fg":
                logging.debug(text)
            if mode == "warn":
                logging.warning(text)
            if mode == "error":
                logging.error(text)
            if mode == "success":
                logging.info(text)
            if mode == "info":
                logging.info(text)
    else:
        if mode == "error":
            click.echo(text, err=True)
        else:
            click.echo(text)


def command(text: str) -> str:
    """Runs a command with subprocess.

    Returns:
        str: The output of the command.
    """
    command_output = subprocess.check_output(text.split()).decode("utf-8")
    output = logging.debug(command_output)
    text_update(output, mode="fg")
    return output


def download_fabric(
    widget, interface: str = "GUI"
) -> str:  # https://github.com/max-niederman/fabric-quick-setup/blob/40c959c6cd2295c679576680fab3cda2b15222f5/fabric_quick_setup/cli.py#L69 (nice)
    """Downloads Fabric's installer.

    Args:
        interface (str, optional): The interface to pass to text_update, either "CLI" or "GUI". Defaults to "GUI".
    Returns:
        str: The path to Fabric's installer.
    """
    tmp = tempfile.mkdtemp(prefix=".fovi-")
    installers = requests.get("https://meta.fabricmc.net/v2/versions/installer").json()
    download = requests.get(installers[0]["url"])
    file_path = tmp + "/" + download.url.split("/")[-1]

    text_update(
        f'Downloading Fabric ({int(download.headers["Content-Length"])//1000} KB)...',
        widget=widget,
        interface=interface,
    )
    with open(file_path, "wb") as file:
        file.write(download.content)
    return file_path


def install_fabric(
    installer_jar: str,
    mc_version: str,
    mc_dir: str,
    widget=None,
    interface: str = "GUI",
) -> None:  # installs the Fabric launcher jar
    """Runs Fabric's installer.

    Args:
        installer_jar (str): Path to the installer jar.
        mc_version (str): The Minecraft version to pass to the script.
        mc_dir (str): The path to the .minecraft directory.
        interface (str, optional): The interface to pass to text_update, either "CLI" or "GUI". Defaults to "GUI".
    """
    text_update("Installing Fabric...", widget)
    ran = command(
        f"{get_java()} -jar {installer_jar} client -mcversion {mc_version} -dir {mc_dir}"
    )

    if ran == 0:
        text_update(
            f"Installed Fabric {mc_version}", widget, "success", interface=interface
        )
    else:
        text_update(
            f"Could not install Fabric: {ran}", widget, "error", interface=interface
        )
    tmp = pathlib.Path(installer_jar).parent.resolve()
    # This will break if Fabric moves away from semver-like things
    # Like if they start doing minor.patch this will break
    # As long as we have MAJOR.Minor.patch we'll be fine
    tmp_regex = str(re.compile("fabric-installer-.*.*.\.jar"))
    tmp = str(rf"{tmp}".replace(f"{tmp_regex}", ""))
    try:
        for existing_file in os.listdir(tmp):
            os.remove(existing_file)
    except OSError as error_code:
        # If an OSError is raised, it's likely that the tmp directory doesn't exist or is empty.
        # There's pretty much no reason to require it, so pass.
        logging.warning(
            f"Temp directory is empty or nonexistent. Skipping deleting all files.\nError details: {error_code}"
        )
    try:
        pathlib.Path(tmp).rmdir()
    except Exception as error_code:
        # Similar situation to above. After all this is a temp dir, so whatever.
        logging.exception(
            f"Could not delete temp directory, leaving in place.\nError details: {error_code}"
        )


def download_pack(widget, interface: str = "GUI") -> str:
    """Downloads the packwiz_install_bootstrap jar.

    Args:
        interface (str, optional): The interface to pass to text_update, either "CLI" or "GUI". Defaults to "GUI".
    Returns:
        str: The path to the packwiz_installer_bootstrap.jar.
    """
    text_update(f"Fetching Pack...", widget=widget, interface=interface)
    download_bootstrap = requests.get(
        "https://github.com/packwiz/packwiz-installer-bootstrap/releases/latest/download/packwiz-installer-bootstrap.jar"
    )
    file_path_bootstrap = get_dir() + "packwiz-installer-bootstrap.jar"
    with open(file_path_bootstrap, "wb") as file:
        file.write(download_bootstrap.content)
    packwiz_installer_bootstrap_path = get_dir() + "packwiz-installer-bootstrap.jar"
    return str(packwiz_installer_bootstrap_path)


def install_pack(
    packwiz_installer_bootstrap: str,
    mc_version: str,
    mc_dir: str,
    widget=None,
    interface: str = "GUI",
):
    """Installs Fabulously Optimized.

    Args:
        packwiz_installer_bootstrap (str): The path to the packwiz installer bootstrap.
        mc_version (str): The version of Minecraft to install for.
        mc_dir (str): The directory to install to.
        widget (optional): The widget to update. Defaults to None.
        interface (str, optional): The interface to pass to text_update, either "CLI" or "GUI". Defaults to "GUI".
    """
    os.chdir(mc_dir)
    os.makedirs(f"{get_dir()}/", exist_ok=True)
    pack_toml = f"https://raw.githubusercontent.com/Fabulously-Optimized/Fabulously-Optimized/main/Packwiz/{mc_version}/pack.toml"
    try:
        ran = command(f"{get_java()} -jar {packwiz_installer_bootstrap} {pack_toml}")
        text_update(
            f"Installed Fabulously Optimized for MC {mc_version}!\nThe installer has finished.",
            widget,
            "success",
            interface=interface,
        )
    except Exception:
        text_update(
            f"Could not install Fabulously Optimized: {ran}",
            widget,
            "error",
            interface=interface,
        )


def run(
    widget=None,
    mc_dir: str = mll.utils.get_minecraft_directory(),
    interface: str = "GUI",
) -> None:
    """Runs Fabric's installer and then installs Fabulously Optimized.

    Args:
        widget (optional): The widget to update. This is only used when interface is set to GUI. Defaults to None.
        mc_dir (str, optional): The directory to use. Defaults to the default directory based on your OS.
        interface (str, optional): The interface to use, either CLI or GUI. Defaults to "GUI".
    """
    text_update("Starting Fabric Download...", widget=widget, interface=interface)
    installer_jar = download_fabric(widget=widget)

    text_update("Starting Fabric Installation...", widget=widget, interface=interface)
    install_fabric(
        installer_jar=installer_jar,
        mc_version=newest_version(),
        mc_dir=mc_dir,
        widget=widget,
        interface=interface,
    )

    text_update("Starting Pack Download...", widget=widget, interface=interface)
    packwiz_bootstrap = download_pack(widget=widget, interface=interface)

    text_update("Starting Pack Installation...", widget=widget, interface=interface)
    install_pack(
        mc_version=newest_version(),
        packwiz_installer_bootstrap=packwiz_bootstrap,
        mc_dir=mc_dir,
        widget=widget,
        interface=interface,
    )


def start_log() -> None:
    """Starts logging for VanillaInstaller."""
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    try:
        handler = logging.handlers.RotatingFileHandler(
            filename="logs/vanilla_installer.log",
            encoding="utf-8",
            maxBytes=32 * 1024 * 1024,  # 32 MiB
            backupCount=5,  # Rotate through 5 files
        )
        dt_fmt = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(
            "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    except Exception:
        # for some reason logging keeps failing, since it's not crucial just pass
        # As such this print()s to stdout
        print("ERROR | Unable to start logging, logging to stdout")
        print("ERROR | Error code: 0xDEADBEEF")

    logging.info("Starting VanillaInstaller")
    logger = logging.getLogger("VanillaInstaller")


if __name__ == "__main__":
    init()  # start initialization
    start_log()  # start logging in case of issues
