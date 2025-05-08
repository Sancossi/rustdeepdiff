from setuptools import setup
from setuptools_rust import Binding, RustExtension

setup(
    name="rustdeepdiff",
    version="0.1.0",
    rust_extensions=[RustExtension("rustdeepdiff.rustdeepdiff", binding=Binding.PyO3)],
    packages=["rustdeepdiff"],
    zip_safe=False,
) 