import base64

import markdown2
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QSizePolicy

from App.utils.Loader import Loader


class MarkdownLabel(QWebEngineView):
    _HIGHLIGHT_SCRIPTS_CACHE = None
    _FONT_BASE64 = None

    def __init__(self, text_or_path, is_path, parent=None):
        super().__init__(parent)
        self._loader = Loader()
        self.current_markdown = None
        self._is_dark = self._loader.is_dark()
        self.mathjax_base_path = self._get_mathjax_base_path()
        self.mathjax_src_path = self._get_mathjax_src_path()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.setMinimumHeight(50)

        initial_text = self._loader.load_text("md/" + text_or_path) if is_path else text_or_path
        self.set_html_from_markdown(initial_text)

    def set_theme(self, is_dark):
        self._is_dark = is_dark
        self.set_html_from_markdown(self.current_markdown)

    def set_markdown(self, text):
        self.current_markdown = text
        self.set_html_from_markdown(text)

    def set_html_from_markdown(self, markdown_text):
        self.current_markdown = markdown_text or ""
        full_html = self._generate_html(self.current_markdown)
        self.setHtml(full_html, baseUrl=QUrl(self.mathjax_base_path))

    # region Helper Methods
    def _get_mathjax_base_path(self):
        path = self._loader.get_path() / "assets" / "bytes" / "mathjax_offline"
        return f"file:///{path}"

    def _get_mathjax_src_path(self):
        path = self._loader.get_path() / "assets" / "bytes" / "mathjax_offline" / "es5"
        return f"file:///{path}/tex-mml-chtml.js"

    @classmethod
    def _load_highlight_scripts(cls):
        if cls._HIGHLIGHT_SCRIPTS_CACHE is None:
            loader = Loader()
            try:
                hljs_script = loader.load_text("highlight/highlight.min.js")
                languages = ["python", "javascript", "java", "cpp", "xml",
                             "css", "sql", "bash", "json", "markdown"]
                lang_scripts = "\n".join(
                    loader.load_text(f"highlight/languages/{lang}.min.js")
                    for lang in languages
                )
                cls._HIGHLIGHT_SCRIPTS_CACHE = (hljs_script, lang_scripts)
            except Exception as e:
                raise Exception(f"Error loading Highlight.js resources: {e}")
        return cls._HIGHLIGHT_SCRIPTS_CACHE

    def _get_highlight_css(self):
        theme = "github-dark" if self._is_dark else "github"
        try:
            return self._loader.load_text(f"highlight/styles/{theme}.min.css")
        except Exception as e:
            raise Exception(f"Error loading Highlight.js theme: {e}")

    @classmethod
    def _get_font_base64(cls):
        if cls._FONT_BASE64 is None:
            loader = Loader()
            font_bytes = loader.load_bytes("fonts/comic-neue-regular.woff2")
            cls._FONT_BASE64 = base64.b64encode(font_bytes).decode("utf-8")
        return cls._FONT_BASE64

    def _get_theme_colors(self):
        return {
            "bg_color": "#31363B" if self._is_dark else "#E6E6E6",
            "text_color": "#E6E6E6" if self._is_dark else "#31363B",
            "code_bg": "#232629" if self._is_dark else "#F0F0F0",
            "border_color": "#7F8C8D" if self._is_dark else "#BDC3C7",
            "link_color": "#1E90FF" if self._is_dark else "#0066CC",
            "table_header_bg": "#2A2E32" if self._is_dark else "#DFE2E5",
            "scrollbar_track": "#1a3d5a" if self._is_dark else "#ffd1dc",
            "scrollbar_thumb": "#2a5a7a" if self._is_dark else "#ffa8ba",
            "scrollbar_hover": "#3a7a9a" if self._is_dark else "#ff8da3"
        }

    def _generate_html(self, markdown_text):
        colors = self._get_theme_colors()
        hljs_script, lang_scripts = self._load_highlight_scripts()
        hljs_css = self._get_highlight_css()
        font_base64 = self._get_font_base64()
        html_body = markdown2.markdown(
            markdown_text,
            extras=["fenced-code-blocks", "tables", "task_list", "footnotes", "toc"]
        )

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            {self._generate_mathjax_script()}
            <style>{hljs_css}</style>
            <script>
                {hljs_script}
                {lang_scripts}
                hljs.highlightAll();
            </script>
            <style>
                {self._generate_css_styles(colors, font_base64)}
            </style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """

    def _generate_mathjax_script(self):
        return f"""
        <script>
        MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true,
                packages: {{'[+]': ['mhchem']}}
            }},
            options: {{
                ignoreHtmlClass: 'tex2jax_ignore',
                processHtmlClass: 'tex2jax_process'
            }},
            loader: {{load: ['[tex]/mhchem']}}
        }};
        </script>
        <script id="MathJax-script" async src="{self.mathjax_src_path}"></script>
        """

    @staticmethod
    def _generate_css_styles(colors, font_base64):
        return f"""
        @font-face {{
            font-family: 'Comic Neue';
            font-style: normal;
            font-weight: 400;
            font-display: swap;
            src: url(data:font/woff2;base64,{font_base64}) format("woff2");
            unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
        }}
        body {{
            font-family: 'Comic Neue', 'Comic Sans MS', 'Marker Felt', 'Arial Rounded MT Bold', 'Arial', sans-serif;
            line-height: 1.6;
            color: {colors['text_color']};
            background-color: {colors['bg_color']};
            padding: 12px;
            margin: 0;
        }}
        a {{
            color: {colors['link_color']};
            text-decoration: none;
        }}
        a:hover {{ text-decoration: underline; }}
        pre {{
            background-color: {colors['code_bg']};
            border-radius: 4px;
            padding: 12px;
            overflow: auto;
            border-left: 3px solid {colors['border_color']};
        }}
        code:not(pre code) {{
            background-color: {colors['code_bg']};
            border-radius: 4px;
            padding: 0.3em 0.5em;
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace, 'Comic Neue';
            color: {colors['text_color']};
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{
            border: 1px solid {colors['border_color']};
            padding: 8px 12px;
        }}
        th {{ background-color: {colors['table_header_bg']}; }}
        blockquote {{
            border-left: 4px solid {colors['border_color']};
            padding-left: 16px;
            margin-left: 0;
            color: {colors['text_color']}99;
        }}
        hr {{
            border: 0;
            height: 1px;
            background-color: {colors['border_color']};
            margin: 20px 0;
        }}
        .MathJax {{
            color: {colors['text_color']} !important;
            background-color: transparent !important;
        }}
        .hljs {{ background: {colors['code_bg']} !important; }}

        /* Scrollbar Styling */
        ::-webkit-scrollbar {{ width: 12px; height: 12px; }}
        ::-webkit-scrollbar-track {{
            background: {colors['scrollbar_track']};
            border-radius: 6px;
        }}
        ::-webkit-scrollbar-thumb {{
            background: {colors['scrollbar_thumb']};
            border-radius: 6px;
            border: 2px solid {colors['scrollbar_track']};
        }}
        ::-webkit-scrollbar-thumb:hover {{ background: {colors['scrollbar_hover']}; }}
        ::-webkit-scrollbar-corner {{ background: {colors['scrollbar_track']}; }}
        """
