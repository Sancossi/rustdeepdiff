import os
import sys
import nox
from nox.command import CommandFailed
from dataclasses import dataclass
import shutil
import glob


@dataclass
class Config:
    DEFAULT_PYTHON_VERSION: str= "3.10"
    CUSTOM_REPO_URL: str= "https://pypi.org/simple"
    USE_VENV: bool= True


# Определяем версию Python из файла .python-version, если он существует
def get_python_version():
    python_version_file = ".python-version"
    if not os.path.exists(python_version_file):
        return Config.DEFAULT_PYTHON_VERSION
    
    with open(python_version_file, "r") as f:
        version = f.read().strip()
        if version.count(".") > 1:
            version = ".".join(version.split(".")[:2])
        return version

# Настройки
PYTHON_VERSION = get_python_version()
CUSTOM_REPO_URL = "https://your-custom-repo-url/simple"  # URL вашего репозитория

# Указываем, что мы используем uv вместо pip
nox.options.default_venv_backend = "uv"


def install_python(version=Config.DEFAULT_PYTHON_VERSION):
    """Установка указанной версии Python, если она отсутствует"""
    try:
        # Проверяем, установлена ли уже нужная версия Python
        import subprocess
        
        # В Windows проверяем по-другому
        if sys.platform == Config.WINDOWS:
            python_cmd = f"py -{version}"
        else:
            python_cmd = f"python{version}"
            
        result = subprocess.run(
            [python_cmd, "--version"] if sys.platform == "win32" else [python_cmd, "--version"], 
            capture_output=True, 
            text=True,
            shell=(sys.platform == "win32")  # Используем shell в Windows
        )
        
        if result.returncode == 0:
            print(f"Python {version} уже установлен: {result.stdout.strip()}")
            return True
    except (FileNotFoundError, subprocess.SubprocessError):
        pass
    
    # Устанавливаем Python в зависимости от ОС
    if sys.platform == Config.LINUX:
        os.system(f"sudo apt-get update && sudo apt-get install -y python{version} python{version}-venv")
    elif sys.platform == Config.MACOS:
        os.system(f"brew install python@{version}")
    elif sys.platform == Config.WINDOWS:
        print(f"Для Windows рекомендуется использовать Python Launcher (py).")
        print(f"Проверьте, установлен ли Python {version} с помощью команды: py -{version} --version")
        print(f"Если нет, скачайте и установите Python {version} с https://www.python.org/downloads/")
        
        # Предлагаем автоматически открыть страницу загрузки
        download_url = f"https://www.python.org/downloads/release/python-{version.replace('.', '')}"
        open_browser = input(f"Открыть страницу загрузки Python {version}? (y/n): ")
        if open_browser.lower() == 'y':
            os.system(f"start {download_url}")
        
        return False
    else:
        print(f"Автоматическая установка Python {version} не поддерживается для этой ОС.")
        print("Пожалуйста, установите Python вручную с https://www.python.org/downloads/")
        return False
    
    return True


def create_venv_win32(session):
    session.run("py", f"-{Config.DEFAULT_PYTHON_VERSION}", "-m", "venv", "venv", external=True)


def create_venv_unix(session):
    session.run("python", "-m", "venv", "venv", external=True)


def create_venv(session):
    if Config.USE_VENV and not os.path.exists("venv"):
        session.log("Создание виртуального окружения...")
        if sys.platform == "win32":
            create_venv_win32(session)
        else:
            create_venv_unix(session)
    
@nox.session(python=Config.DEFAULT_PYTHON_VERSION)
def setup(session):
    """Настройка окружения: установка Python и создание venv"""

    if sys.platform == Config.WINDOWS:
        try:
            session.run("py", f"-{Config.DEFAULT_PYTHON_VERSION}", "--version", external=True)
            print(f"Python {Config.DEFAULT_PYTHON_VERSION} уже установлен")
        except:
            session.error(f"Python {Config.DEFAULT_PYTHON_VERSION} не найден. Пожалуйста, установите его вручную.")
    else:
        if not install_python(Config.DEFAULT_PYTHON_VERSION):
            session.error(f"Не удалось установить Python {Config.DEFAULT_PYTHON_VERSION}")
    
    if Config.USE_VENV and not os.path.exists("venv"):
        session.log("Создание виртуального окружения...")
        if sys.platform == "win32":
            session.run("py", f"-{Config.DEFAULT_PYTHON_VERSION}", "-m", "venv", "venv", external=True)
        else:
            session.run("python", "-m", "venv", "venv", external=True)
        
        venv_pip = os.path.join("venv", "bin", "pip") if sys.platform != "win32" else os.path.join("venv", "Scripts", "pip")
        session.run(venv_pip, "install", "uv", external=True)


@nox.session(python=["3.7", "3.8", "3.9", "3.10", "3.11"])
def tests(session):
    session.install("maturin")
    session.install("pytest")
    session.run("maturin", "develop", "--release")
    session.run("pytest", "tests")


@nox.session
def lint(session):
    session.install("ruff")
    session.run("ruff", "check", "python")


@nox.session(python=Config.DEFAULT_PYTHON_VERSION)
def build(session):
    """Сборка проекта с использованием maturin"""
    session.install("--index-url", Config.CUSTOM_REPO_URL, "maturin>=1.0,<2.0")
    
    session.run("maturin", "build", "--release")
    
    session.log("Сборка завершена. Проверьте директорию target/wheels/")
    
    if session.posargs and "sdist" in session.posargs:
        session.run("maturin", "sdist")
        session.log("Создан source distribution (sdist)")


@nox.session(python=Config.DEFAULT_PYTHON_VERSION)
def format(session):
    """Форматирование кода"""
    session.install("--index-url", Config.CUSTOM_REPO_URL, "black", "isort")
    session.run("black", "src")
    session.run("isort", "src")


@nox.session(python=Config.DEFAULT_PYTHON_VERSION)
def package(session):
    """Создание и проверка пакета для публикации"""
    session.install("--index-url", Config.CUSTOM_REPO_URL, "maturin>=1.0,<2.0", "twine", "build")
    
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("target/wheels"):
        for file in glob.glob("target/wheels/*.whl"):
            os.remove(file)
    
    session.run("maturin", "build", "--release")
    
    session.run("maturin", "sdist")
    
    os.makedirs("dist", exist_ok=True)
    for wheel in glob.glob("target/wheels/*.whl"):
        shutil.copy(wheel, "dist/")
    
    session.run("twine", "check", "dist/*")
    
    session.log("Пакеты успешно созданы и проверены. Они находятся в директории dist/")
    session.log("Для публикации используйте: twine upload dist/*")


@nox.session(python=Config.DEFAULT_PYTHON_VERSION)
def py_package(session):
    """Создание чистого Python-пакета без Rust-компонентов"""
    session.install("--index-url", Config.CUSTOM_REPO_URL, "build", "twine")
    
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    temp_dir = "temp_py_package"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    python_src = "python"
    if os.path.exists(python_src):
        shutil.copytree(python_src, os.path.join(temp_dir, "python"))
    
    with open("pyproject.toml", "r", encoding="utf-8") as f:
        pyproject_content = f.read()
        
        pyproject_content = pyproject_content.replace(
            "[build-system]\nrequires = [\"maturin>=1.0,<2.0\"]\nbuild-backend = \"maturin\"",
            "[build-system]\nrequires = [\"setuptools>=42\", \"wheel\"]\nbuild-backend = \"setuptools.build_meta\""
        )
        
        with open(os.path.join(temp_dir, "pyproject.toml"), "w") as f:
            f.write(pyproject_content)
    
    for file in ["README.md", "LICENSE"]:
        if os.path.exists(file):
            shutil.copy(file, os.path.join(temp_dir, file))
    
    setup_py = """
from setuptools import setup, find_packages

setup(
    name="py-rustdeepdiff",
    packages=find_packages(where="python"),
    package_dir={"": "python"},
)
"""
    with open(os.path.join(temp_dir, "setup.py"), "w") as f:
        f.write(setup_py)
    
    with session.chdir(temp_dir):
        session.run("python", "-m", "build", "--wheel", "--sdist")
        
        os.makedirs("../dist", exist_ok=True)
        for file in glob.glob("dist/*"):
            shutil.copy(file, "../dist/")
    
    session.run("twine", "check", "dist/*")
    
    shutil.rmtree(temp_dir)
    
    session.log("Python-пакет успешно создан и проверен. Файлы находятся в директории dist/")
    session.log("Для публикации используйте: twine upload dist/py-rustdeepdiff*")
