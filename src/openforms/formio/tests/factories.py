import factory
from furl import furl

from openforms.submissions.tests.factories import TemporaryFileUploadFactory


class _SubmittedFileDataFactory(factory.DictFactory):
    url = factory.SelfAttribute("..url")
    form = ""
    name = factory.SelfAttribute("..name")
    size = factory.SelfAttribute("..size")
    baseUrl = factory.LazyAttribute(lambda d: furl(d.factory_parent.url).origin)
    project = ""


class SubmittedFileFactory(factory.DictFactory):
    name = factory.Sequence(lambda n: f"foo-{n}.bin")
    originalName = factory.LazyAttribute(lambda obj: obj.name)
    size = factory.Faker("pyint", min_value=1)
    storage = "url"
    type = "application/foo"
    url = "http://localhost/api/v2/submissions/files/123"
    data = factory.SubFactory(_SubmittedFileDataFactory)

    @factory.post_generation
    def temporary_upload(obj, create, extracted, **kwargs):
        if extracted:
            # The temporary upload was explicitly provided, read the necessary values from there
            temporary_upload = extracted
            obj["data"]["name"] = kwargs.get("data_name") or temporary_upload.file_name
            obj["originalName"] = (
                kwargs.get("original_name") or temporary_upload.file_name
            )
            obj["size"] = obj["data"]["size"] = temporary_upload.file_size
        else:
            create_temporary_upload = (
                TemporaryFileUploadFactory.create
                if create
                else TemporaryFileUploadFactory.build
            )
            temporary_upload = create_temporary_upload(
                file_name=obj["name"], file_size=obj["size"], **kwargs
            )
        new_url = f"http://localhost/api/v2/submissions/files/{temporary_upload.uuid}"
        obj["url"] = obj["data"]["url"] = new_url
