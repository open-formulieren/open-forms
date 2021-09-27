from django.core.exceptions import ValidationError
from django.test import TestCase

from relativedeltafield import RelativeDeltaField
from .testapp.models import Interval

from datetime import timedelta
from dateutil.relativedelta import relativedelta

class RelativeDeltaFieldTest(TestCase):
	def setUp(self):
		Interval.objects.all().delete()

	def assertStrictEqual(self, a, b):
		self.assertEqual(a, b)
		self.assertEqual(type(a), type(b))


	def test_basic_value_survives_db_roundtrip(self):
		input_value = relativedelta(years=2,months=3,days=4,hours=5,minutes=52,seconds=30,microseconds=5)
		obj = Interval(value=input_value)
		obj.save()

		obj.refresh_from_db()
		self.assertStrictEqual(input_value, obj.value)


	def test_empty_value_survives_db_roundtrip(self):
		obj = Interval(value=relativedelta())
		obj.save()

		obj.refresh_from_db()
		self.assertStrictEqual(relativedelta(), obj.value)


	def test_each_separate_value_survives_db_roundtrip(self):
		values = {
			'years': 501,
			'months': 10,
			'days': 2,
			'hours': 1,
			'minutes': 52,
			'seconds': 12,
		}

		for k in values:
			input_value = relativedelta(**{k: values[k]})
			obj = Interval(value=input_value)
			obj.save()

			obj.refresh_from_db()
			# Put the object in a dict to get descriptive output on failure
			self.assertEqual({k: input_value}, {k: obj.value})
			self.assertEqual({k: int}, {k: type(getattr(obj.value, k))})


	# See issue #2, we should not serialize weeks separately, because
	# it is a derived value.
	def test_weeks_value_survives_db_roundtrip_as_days(self):
		input_value = relativedelta(weeks=2,days=1)
		obj = Interval(value=input_value)
		obj.save()

		obj.refresh_from_db()
		self.assertStrictEqual(15, obj.value.days)
		self.assertStrictEqual(2, obj.value.weeks)


	def test_none_value_also_survives_db_roundtrip(self):
		obj = Interval(value=None)
		obj.save()

		obj.refresh_from_db()
		self.assertIsNone(obj.value)


	def test_none_value_survives_full_clean(self):
		obj = Interval(value=None)
		obj.full_clean()
		self.assertIsNone(obj.value)


	# Specific check, because to_python doesn't get called by save()
	# or full_clean() when the value is None (but other things might)
	# This is a regression test for a bug where we'd call normalized()
	# even on None values.
	def test_none_value_survives_to_python(self):
		self.assertIsNone(RelativeDeltaField().to_python(None))


	def test_value_is_normalized_on_full_clean(self):
		input_value = relativedelta(years=1,months=3,weeks=1,days=4.5,hours=5,minutes=70.5,seconds=80.100005,microseconds=5)
		obj = Interval(value=input_value)
		obj.full_clean()

		self.assertNotEqual(input_value, obj.value)
		self.assertStrictEqual(input_value.normalized(), obj.value)

		# Quick sanity check to ensure the input isn't mutated.
		# Take into account that weeks are added to days though!
		self.assertStrictEqual(11.5, input_value.days)
		self.assertStrictEqual(1, input_value.weeks)

		# Check that the values are normalized
		self.assertStrictEqual(1, obj.value.years)
		self.assertStrictEqual(3, obj.value.months)
		self.assertStrictEqual(11, obj.value.days)
		self.assertStrictEqual(18, obj.value.hours)
		self.assertStrictEqual(11, obj.value.minutes)
		self.assertStrictEqual(50, obj.value.seconds)
		self.assertStrictEqual(100010, obj.value.microseconds)

		# Derived value, from the number of days (see #2); but it's no
		# longer converted to a floating-point number in newer
		# versions of relativedelta....
		self.assertStrictEqual(1, obj.value.weeks)


	def test_weeks_value_is_derived_as_int_when_normalizing_on_full_clean(self):
		input_value = relativedelta(years=1,months=3,weeks=1,days=11.5,hours=5,minutes=70.5,seconds=80.100005,microseconds=5)
		obj = Interval(value=input_value)
		obj.full_clean()

		self.assertNotEqual(input_value, obj.value)
		self.assertStrictEqual(input_value.normalized(), obj.value)

		# Quick sanity check to ensure the input isn't mutated.
		# Take into account that weeks are added to days though!
		self.assertStrictEqual(18.5, input_value.days)
		self.assertStrictEqual(2, input_value.weeks)

		# Derived value, from the number of days (see #2)
		self.assertStrictEqual(2, obj.value.weeks)


	def test_string_input(self):
		obj = Interval(value='P1Y3M1W4.5DT5H70.5M80.10001S')
		obj.full_clean()

		self.assertIsInstance(obj.value, relativedelta)

		# Check that the values are normalized
		self.assertStrictEqual(1, obj.value.years)
		self.assertStrictEqual(3, obj.value.months)
		self.assertStrictEqual(11, obj.value.days)
		self.assertStrictEqual(18, obj.value.hours)
		self.assertStrictEqual(11, obj.value.minutes)
		self.assertStrictEqual(50, obj.value.seconds)
		self.assertStrictEqual(100010, obj.value.microseconds)

		# Derived value, from the number of days (see #2)
		self.assertStrictEqual(1, obj.value.weeks)


	def test_invalid_string_inputs_raise_validation_error(self):
		obj = Interval()

		obj.value = 'blabla'
		with self.assertRaises(ValidationError) as cm:
			obj.full_clean()
		self.assertEqual(set(['value']), set(cm.exception.message_dict.keys()))

		obj.value = 'P1.5M' # not allowed by relativedelta because it is supposedly ambiguous
		with self.assertRaises(ValidationError) as cm:
			obj.full_clean()
		self.assertEqual(set(['value']), set(cm.exception.message_dict.keys()))

		obj.value = 'P1M' # Check that the error is cleared when made valid again
		obj.full_clean()


	def test_invalid_objects_raise_validation_errors(self):
		obj = Interval()

		obj.value = True
		with self.assertRaises(ValidationError) as cm:
			obj.full_clean()
		self.assertEqual(set(['value']), set(cm.exception.message_dict.keys()))

		obj.value = 1
		with self.assertRaises(ValidationError) as cm:
			obj.full_clean()
		self.assertEqual(set(['value']), set(cm.exception.message_dict.keys()))

		obj.value = 'P1M' # Check that the error is cleared when made valid again
		obj.full_clean()


	def test_timedelta_input(self):
		td = timedelta(weeks=1,days=4.5,hours=5,minutes=70.5,seconds=80.100005,microseconds=5)
		obj = Interval(value=td)
		obj.full_clean()

		self.assertIsInstance(obj.value, relativedelta)

		# Check that the values are normalized
		self.assertStrictEqual(0, obj.value.years)
		self.assertStrictEqual(0, obj.value.months)
		self.assertStrictEqual(11, obj.value.days)
		self.assertStrictEqual(18, obj.value.hours)
		self.assertStrictEqual(11, obj.value.minutes)
		self.assertStrictEqual(50, obj.value.seconds)
		self.assertStrictEqual(100010, obj.value.microseconds)

		# Derived value, from the number of days (see #2)
		self.assertStrictEqual(1, obj.value.weeks)


	def test_filtering_works(self):
		obj1 = Interval(value='P1Y3M1W4.5DT5H70.5M80.10001S')
		obj1.save()

		obj2 = Interval(value='P12D')
		obj2.save()

		q = Interval.objects.filter(value__gt='P1Y')
		self.assertEqual(1, q.count())

		q = Interval.objects.filter(value__lt='P2Y')
		self.assertEqual(2, q.count())
