# Удаляем старую установку
pip uninstall -y rustdeepdiff

# Очищаем кэш
rm -rf build/ dist/ target/

# Пересобираем и устанавливаем
maturin develop --release

# Или через nox
nox -s build
pip install target/wheels/rustdeepdiff-0.1.0-*.whl 