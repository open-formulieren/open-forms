from django.test import TestCase

from openforms.accounts.models import User
from openforms.products.models import Product

from ..models import Form, FormDefinition, FormStep


class BaseFormTestCase(TestCase):

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username='test',
            password='secret',
            email='user@gmail.com'
        )
        self.product = Product.objects.create(name='Frozen Banana', price=5)
        self.form = Form.objects.create(
            name='Banana Stand',
            slug='banana-stand',
            product=self.product,
            active=True
        )

        self.form_def_1 = FormDefinition.objects.create(
            name='Hermanos',
            slug='hermanos',
            configuration={
                'test-form-data': []
            }
        )

        self.form_def_2 = FormDefinition.objects.create(
            name='Illusion Michael',
            slug='illusion-michael',
            login_required=True,
            configuration={
                'test-form-data-2': []
            }
        )
        self.form_step_1 = FormStep.objects.create(
            order=0,
            form=self.form,
            form_definition=self.form_def_1
        )
        self.form_step_2 = FormStep.objects.create(
            order=1,
            form=self.form,
            form_definition=self.form_def_2
        )
