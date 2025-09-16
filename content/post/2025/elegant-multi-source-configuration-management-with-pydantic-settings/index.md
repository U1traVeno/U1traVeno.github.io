---
date: '2025-08-02T16:46:15+08:00'
draft: false
title: '使用Pydantic Settings优雅地管理多来源的应用配置'
tags: ['Python', 'Pydantic', 'Typer']
comments: true
---

场景： 我们希望从多种来源，从配置文件导入我们的配置，并且经过 Pydantic 校验。`pydantic-settings`库提供了方便的API供我们实现这一需求。

[**Pydantic - Settings Management**](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

下面直接给出代码示例。

```python
# config.py

import os
from pathlib import Path
from typing import Any, Self
from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    InitSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
    YamlConfigSettingsSource,
)


class EnvVarFileConfigSettingsSource(InitSettingsSource):
    """
    A source that loads configuration from a file specified in an environment variable.
    It automatically selects the TOML or YAML parser based on the file extension.
    """

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        env_var: str = "MYAPP_CONFIG_FILE",
        env_file_encoding: str | None = None,
    ):
        """
        Args:
            settings_cls: The settings class.
            env_var: The name of the environment variable to read the file path from.
            env_file_encoding: The encoding to use for YAML files.
        """
        self.env_var = env_var
        self.file_path_str = os.getenv(env_var)
        self.encoding = env_file_encoding

        file_data: dict[str, Any] = {}

        if not self.file_path_str:
            super().__init__(settings_cls, file_data)
            return

        file_path = Path(self.file_path_str)
        if not file_path.exists():
            print(
                f"Warning: The file '{file_path}' pointed to by the environment variable '{self.env_var}' does not exist."
            )

        # Reuse existing source logic based on file extension
        suffix = file_path.suffix.lower()
        if suffix == ".toml":
            # Internally create a TomlConfigSettingsSource instance to load the file
            file_data = TomlConfigSettingsSource(
                settings_cls, toml_file=file_path
            ).toml_data
        elif suffix in (".yaml", ".yml"):
            # Internally create a YamlConfigSettingsSource instance to load the file
            file_data = YamlConfigSettingsSource(
                settings_cls, yaml_file=file_path, yaml_file_encoding=self.encoding
            ).yaml_data
        else:
            print(f"Warning: Unsupported file type '{suffix}'. Ignored.")

        # Call InitSettingsSource's __init__, passing the data loaded from the file
        super().__init__(settings_cls, file_data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(env_var={self.env_var}, file_path={self.file_path_str!r})"


class DatabaseConfig(BaseModel):
    postgres_user: str = "veno"
    postgres_password: str = "12345678"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "veno_db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        toml_file=Path("myapp.toml"),
        yaml_file=Path("myapp.yaml") or Path("myapp.yml"),
        yaml_file_encoding="utf-8",
        env_prefix="MYAPP_",
        env_nested_delimiter="__",
    )

    debug: bool = False
    formal: bool = True
    database: DatabaseConfig = DatabaseConfig()

    @classmethod
    def settings_customise_sources(
        cls: type[Self],
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Define the priority of different configuration sources.
        See: https://docs.pydantic.dev/latest/concepts/pydantic_settings/#customise-settings-sources
        """
        return (
            init_settings,
            # Custom Source
            EnvVarFileConfigSettingsSource(settings_cls),
            # env_settings,
            dotenv_settings,
            # See: https://docs.pydantic.dev/latest/concepts/pydantic_settings/#other-settings-source
            TomlConfigSettingsSource(settings_cls),
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


settings = Settings()


# main.py

import os
from typing import Annotated
import typer

import playground.config as config_module

cli_app = typer.Typer()
env_config_file = "MYAPP_CONFIG_FILE"


@cli_app.command()
def hello(name: Annotated[str, typer.Option()] = "Veno"):
    print(f"Hello, {name}")
    if config_module.settings.debug:
        print(f"cli_app: {cli_app}")


@cli_app.command()
def bye():
    if config_module.settings.formal:
        print("Goodbye!")
    else:
        print("See ya!")


@cli_app.callback()
def main(config: Annotated[str | None, typer.Option()] = None):
    if config:
        os.environ[env_config_file] = str(config)
        config_module.settings.__init__()


if __name__ == "__main__":
    cli_app()

```

我们定义了一个`Settings(BaseSettings)`类，这是我们的应用配置类。我们可以在其中定义应用配置项，或是嵌套其他的子配置类。子配置类不需要再继承`BaseSettings`, 而是继承`BaseModel`。

`Settings`类中，我们可以通过自定义`settings_customise_sources`方法中返回的元组内元素的顺序，调整 Pydantic 导入配置源的优先级。靠前的配置源中配置项的值将不会被靠后的配置源的配置项值所覆盖。靠前的配置源成功读取之后并不会略过之后的配置源。也就是说，如果某一项配置值在靠前的配置源未出现，但在靠后的配置源出现，则会使用该出现的值。

如果我们希望删除某个配置源，那么我们可以从返回的元组中剔除它（如本例的`env_settings`）。

要导入新的配置源，同样也可以在返回的元组中添加它们。本例添加了 `TomlConfigFileSettingsSource`，`YamlConfigFileSettingsSource`。它们会从`Settings`类的`model_config`中的`toml_file`等变量获取配置文件位置。例如这里会获取运行根目录下的`myapp.toml`。

```python
# pydantic_settings/sources/providers/toml.py
class TomlConfigSettingsSource(InitSettingsSource, ConfigFileSourceMixin):
    """
    A source class that loads variables from a TOML file
    """

    def __init__(
        self,
        settings_cls: type[BaseSettings],
        toml_file: PathType | None = DEFAULT_PATH,
    ):
        self.toml_file_path = toml_file if toml_file != DEFAULT_PATH else settings_cls.model_config.get('toml_file')
        self.toml_data = self._read_files(self.toml_file_path)
        super().__init__(settings_cls, self.toml_data)

    def _read_file(self, file_path: Path) -> dict[str, Any]:
        import_toml()
        with open(file_path, mode='rb') as toml_file:
            if sys.version_info < (3, 11):
                return tomli.load(toml_file)
            return tomllib.load(toml_file)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(toml_file={self.toml_file_path})'
```

这里我们自定义了一个从`env_var`读取配置文件位置的`EnvVarFileConfigSettingsSource`类，并希望它被优先使用。当`MYAPP_CONFIG_FILE`环境变量被设置时，它会试图读取 TOML 或 YAML 配置文件。

在`main.py`中，我们设置了一个 typer 的回调函数，为主 CLI 应用本身添加了`--config`参数用于指定配置文件位置。用户如果指定了该参数，则会设置`MYAPP_CONFIG_FILE`环境变量，并重载`settings`实例。参见: [Pydantic - Settings Management - In-place reloading](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#in-place-reloading)
