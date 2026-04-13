from django import forms
from .models import News
from .models import Comment

class NewsForm(forms.ModelForm):
    tags = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Enter tags separated by commas'}))

    class Meta:
        model = News
        fields = ['title', 'content', 'image', 'category', 'breaking']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['tags'].initial = ', '.join(tag.name for tag in self.instance.tags.all())


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']