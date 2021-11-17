from rest_framework import serializers


class ConfirmationEmailTemplateSerializer(serializers.Serializer):
    """
    The reason this is not a ModelSerializer is we want to allow

    ```
    {
       'subject': '',
       'content': ''
    }
    ```

    to be passed in through the API without this serializer raising a ValidationError
    """

    subject = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    content = serializers.CharField(required=False, allow_blank=True)
