from pybuilder.core import use_plugin, init, Author

use_plugin("python.core")
use_plugin("python.unittest")
use_plugin("python.install_dependencies")
use_plugin("python.flake8")
use_plugin("python.frosted")
use_plugin("python.coverage")
use_plugin("python.distutils")


name = "netkraken-minion"
description = """records network connections: source host, protocol, target host"""
summary = description
authors = [Author("Arne Hilmann", "arne.hilmann@gmail.com")]
url = "https://github.com/netkraken/minion"
version = "0.1"

default_task = "publish"


@init
def set_properties(project):
    project.build_depends_on("mock")
    project.depends_on("docopt")
    project.depends_on("countdb")

    project.set_property("flake8_verbose_output", True)
    project.set_property("flake8_break_build", True)
