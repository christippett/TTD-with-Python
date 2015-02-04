from django.test import TestCase
from django.core.urlresolvers import resolve
from django.http import HttpRequest
from django.template.loader import render_to_string
from lists.models import Item, List
from lists.views import home_page, view_list # home_page is the view function stored in lists/views.py
from django.utils.html import escape

class HomePageTest(TestCase):
	
	def test_root_url_resolves_to_home_page_view(self):
		found = resolve('/') # function Django uses internally to resolve URLs and find what view function they should be mapped to
		self.assertEqual(found.func, home_page) # Check that resolve, when called with '/', finds a function called home_page
		
	def test_home_page_returns_correct_html(self):
		request = HttpRequest() # An HttpRequest object, this is what Django sees when a user's browser asks for a page
		response = home_page(request) # We pass this request to our home_page view, which gives a reponse in form of an HttpResponse object
		expected_html = render_to_string('home.html')
		self.assertEqual(response.content.decode(), expected_html)
		
		self.assertTrue(response.content.startswith(b'<!DOCTYPE html>'))
		self.assertIn(b'<title>To-Do lists</title>', response.content)
		self.assertTrue(response.content.endswith(b'</html>'))

class ListsViewTest(TestCase):

	def test_uses_list_template(self):
		list_ = List.objects.create()
		response = self.client.get('/lists/%d/' % (list_.id))
		self.assertTemplateUsed(response, 'list.html')

	def test_displays_only_items_for_that_list(self):
		correct_list = List.objects.create()
		Item.objects.create(text='itemey 1', list=correct_list)
		Item.objects.create(text='itemey 2', list=correct_list)

		other_list = List.objects.create()
		Item.objects.create(text='other list item 1', list=other_list)
		Item.objects.create(text='other list item 2', list=other_list)

		# Instead of calling the view function directly, we use
		# the Django test client, which is an attribute of the
		# Django TestCase called self.client
		response = self.client.get('/lists/%d/' % (correct_list.id))

		# Django's assertContains method knows how to deal with
		# responses and the bytes of their content (no need for .decode())
		self.assertContains(response, 'itemey 1')
		self.assertContains(response, 'itemey 2')
		self.assertNotContains(response, 'other list item 1')
		self.assertNotContains(response, 'other list item 2')

		# # Old way of testing:
		# request = HttpRequest()
		# response = view_list(request)
		
		# self.assertIn('itemey 1', response.content.decode())
		# self.assertIn('itemey 2', response.content.decode())

	def test_passes_correct_list_to_template(self):
		other_list = List.objects.create()
		correct_list = List.objects.create()
		response = self.client.get('/lists/%d/' % (correct_list.id,))
		self.assertEqual(response.context['list'], correct_list) # response.context represents the context passed to the render function


class NewListTest(TestCase):

	def test_saving_a_POST_request(self):
		# request = HttpRequest()
		# request.method = 'POST'
		# request.POST['item_text'] = 'A new list item'
		
		# response = home_page(request)

		self.client.post(
			'/lists/new',
			data={'item_text': 'A new list item'}
		)
		
		self.assertEqual(Item.objects.count(), 1)
		new_item = Item.objects.first()
		self.assertEqual(new_item.text, 'A new list item')
		
	def test_redirects_after_POST(self):
		response = self.client.post(
			'/lists/new',
			data={'item_text': 'A new list item'}
		)
		
		new_list = List.objects.first()
		self.assertRedirects(response, '/lists/%d/' % (new_list.id,))

	def test_validation_errors_are_sent_back_to_home_page_template(self):
		response = self.client.post('/lists/new', data={'item_text': ''})
		self.assertEqual(response.status_code, 200)
		self.assertTemplateUsed(response, 'home.html')
		expected_error = escape("You can't have an empty list item")
		self.assertContains(response, expected_error)

	def test_invalid_list_items_arent_saved(self):
		self.client.post('/lists/new', data={'item_text': ''})
		self.assertEqual(List.objects.count(), 0)
		self.assertEqual(Item.objects.count(), 0)

class NewItemTest(TestCase):

	def test_can_save_a_POST_request_to_an_existing_list(self):
		other_list = List.objects.create()
		correct_list = List.objects.create()

		self.client.post(
			'/lists/%d/add_item' % (correct_list.id,),
			data={'item_text': 'A new item for an existing list'}
		)

		self.assertEqual(Item.objects.count(), 1)
		new_item = Item.objects.first()
		self.assertEqual(new_item.text, 'A new item for an existing list')
		self.assertEqual(new_item.list, correct_list)

	def test_redirects_to_list_view(self):
		other_list = List.objects.create()
		correct_list = List.objects.create()

		response = self.client.post(
			'/lists/%d/add_item' % (correct_list.id,),
			data={'item_text': 'A new item for an existing list'}
		)

		self.assertRedirects(response, '/lists/%d/' % (correct_list.id,))

		
		