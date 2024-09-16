"""
 * Copyright 2020 The Backstage Authors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
"""

import tempfile
import logging
import os
from mkdocs.plugins import BasePlugin
from mkdocs.theme import Theme
from mkdocs.contrib.search import SearchPlugin
from material.plugins.search.plugin import SearchPlugin as MaterialSearchPlugin
from mkdocs_monorepo_plugin.plugin import MonorepoPlugin
from pymdownx.emoji import to_svg
from pymdownx.extra import extra_extensions

log = logging.getLogger(__name__)

TECHDOCS_DEFAULT_THEME = "material"


class TechDocsCore(BasePlugin):
    def __init__(self):
        # This directory will be removed automatically once the docs are built
        # MkDocs needs a directory for the theme with the `techdocs_metadata.json` file
        self.tmp_dir_techdocs_theme = tempfile.TemporaryDirectory()

    def on_config(self, config):
        with open(
            os.path.join(self.tmp_dir_techdocs_theme.name, "techdocs_metadata.json"),
            "w+",
        ) as fp:
            fp.write(
                '{{ {"site_name": (config.site_name | string), '
                '"site_description": (config.site_description | string)} | tojson }}'
            )

        # Core configurations that should take precedence
        core_configs = {
            "pymdownx.snippets": {
                "restrict_base_path": True,
            },
            # Add other core configurations here if needed
        }

        # Merge core configurations with user configurations
        def merge_configs(core, user):
            for key, value in core.items():
                if isinstance(value, dict) and key in user:
                    merge_configs(value, user[key])
                else:
                    user[key] = value

        # Apply core configurations
        if "mdx_configs" not in config:
            config["mdx_configs"] = {}

        merge_configs(core_configs, config["mdx_configs"])

        # Theme
        if config["theme"].name != TECHDOCS_DEFAULT_THEME:
            config["theme"] = Theme(name=TECHDOCS_DEFAULT_THEME)
        elif config["theme"].name == TECHDOCS_DEFAULT_THEME:
            log.info(
                "[mkdocs-techdocs-core] Overridden '%s' theme settings in use",
                TECHDOCS_DEFAULT_THEME,
            )

        if "features" not in config["theme"]:
            config["theme"]["features"] = []

        config["theme"]["features"].append("navigation.footer")
        config["theme"]["features"].append("content.action.edit")

        config["theme"]["palette"] = {}

        config["theme"].static_templates.update({"techdocs_metadata.json"})
        config["theme"].dirs.append(self.tmp_dir_techdocs_theme.name)

        # Plugins
        use_material_search = config["plugins"]["techdocs-core"].config.get(
            "use_material_search", False
        )
        del config["plugins"]["techdocs-core"]

        if use_material_search:
            search_plugin = MaterialSearchPlugin()
        else:
            search_plugin = SearchPlugin()
        search_plugin.load_config({})

        monorepo_plugin = MonorepoPlugin()
        monorepo_plugin.load_config({})
        config["plugins"]["search"] = search_plugin
        config["plugins"]["monorepo"] = monorepo_plugin

        # Markdown Extensions
        if "markdown_extensions" not in config:
            config["markdown_extensions"] = []

        def merge_extension(extension, default_config):
            if extension not in config["markdown_extensions"]:
                config["markdown_extensions"].append(extension)
            if extension in config["mdx_configs"]:
                config["mdx_configs"][extension].update(default_config)
            else:
                config["mdx_configs"][extension] = default_config

        merge_extension("admonition", {})
        merge_extension("toc", {"permalink": True})
        merge_extension("pymdownx.caret", {})
        merge_extension("pymdownx.critic", {})
        merge_extension("pymdownx.details", {})
        merge_extension("pymdownx.emoji", {"emoji_generator": to_svg})
        merge_extension("pymdownx.inlinehilite", {})
        merge_extension("pymdownx.magiclink", {})
        merge_extension("pymdownx.mark", {})
        merge_extension("pymdownx.smartsymbols", {})
        merge_extension("pymdownx.snippets", {})
        merge_extension(
            "pymdownx.highlight", {"linenums": True, "pygments_lang_class": True}
        )
        merge_extension("pymdownx.extra", {"smart_enable": "all"})
        merge_extension("pymdownx.tabbed", {"alternate_style": True})
        merge_extension("pymdownx.tasklist", {"custom_checkbox": True})
        merge_extension("pymdownx.tilde", {})
        merge_extension("markdown_inline_graphviz", {})
        merge_extension("plantuml_markdown", {})
        merge_extension("mdx_truly_sane_lists", {})

        # Merge individual extension configs under the pymdownx.extra extension namespace if individual extension is supplied by pymdownx.extra
        # https://facelessuser.github.io/pymdown-extensions/extensions/extra/
        if "pymdownx.extra" not in config["mdx_configs"]:
            config["mdx_configs"]["pymdownx.extra"] = {}
        for extension in extra_extensions:
            if extension in config["mdx_configs"]:
                config["mdx_configs"]["pymdownx.extra"][extension] = config[
                    "mdx_configs"
                ][extension]
                del config["mdx_configs"][extension]

        return config
