import json

from django import forms

from apps.core.models import PageContent, Section


class _Styled:
    def _style(self):
        for f in self.fields.values():
            if not isinstance(f.widget, (forms.CheckboxInput, forms.HiddenInput)):
                f.widget.attrs.setdefault("class", "input")


class SectionForm(_Styled, forms.ModelForm):
    ITEMS_HELP = "One item per line, parts separated by |"

    class Meta:
        model = Section
        fields = ["page", "kind", "is_active", "style", "order", "eyebrow", "title", "highlight", "title_end",
                  "subtitle", "body", "items", "image", "button_text", "button_url", "button2_text",
                  "button2_url", "limit", "show_details"]
        widgets = {
            "page": forms.HiddenInput,
            "subtitle": forms.Textarea(attrs={"rows": 3}),
            "body": forms.Textarea(attrs={"rows": 8, "class": "input mono"}),
            "items": forms.Textarea(attrs={"rows": 6, "class": "input mono"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["items"].help_text = self.ITEMS_HELP
        self._style()

    @property
    def kind_fields_json(self):
        return json.dumps(Section.FIELDS)

    @property
    def item_help_json(self):
        return json.dumps(Section.ITEM_HELP)


class PageForm(_Styled, forms.ModelForm):
    BUILTIN_FIELDS = ["show_hero", "eyebrow", "heading", "highlight", "heading_end", "lead",
                      "meta_title", "meta_description"]

    class Meta:
        model = PageContent
        fields = ["title", "slug", "is_published", "show_hero", "eyebrow", "heading", "highlight",
                  "heading_end", "lead", "button_text", "button_url", "button2_text", "button2_url",
                  "meta_title", "meta_description"]
        widgets = {"lead": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and self.instance.is_builtin:
            for name in ["title", "slug"]:
                self.fields.pop(name)
            if self.instance.page == "home":
                self.fields.pop("is_published")
        self._style()
