from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Cat, Toy, Photo
from .forms import FeedingForm

import uuid
import boto3


S3_BASE_URL = 'https://s3.us-east-1.amazonaws.com/'
BUCKET = 'catcollector-db-3'

# Create your views here.

# def home(request):
#     '''
#     this is where we return a response
#     in most cases we  would render a template
#     and we'll need some data for that template
#     '''
#     return HttpResponse('<h1> Hello World </h1>')

def home(request):
  return render(request, 'home.html')

def about(request):
  return render(request, 'about.html')

@login_required
def cats_index(request):
  cats = Cat.objects.filter(user=request.user)
  return render(request, 'cats/index.html', { 'cats': cats })

@login_required
def cats_detail(request, cat_id):
  cat = Cat.objects.get(id=cat_id)
  feeding_form = FeedingForm()
  toys_cat_doesnt_have = Toy.objects.exclude(id__in = cat.toys.all().values_list('id'))
  return render(request, 'cats/detail.html', {
    # include the cat and feeding_form in the context
    'cat': cat, 'feeding_form': feeding_form,
    'toys': toys_cat_doesnt_have
  })

@login_required
def add_feeding(request, cat_id):
  # create the ModelForm using the data in request.POST
  form = FeedingForm(request.POST)
  # validate the form
  if form.is_valid():
    # don't save the form to the db until it
    # has the cat_id assigned
    new_feeding = form.save(commit=False)
    new_feeding.cat_id = cat_id
    new_feeding.save()
  return redirect('detail', cat_id=cat_id)


@login_required
def assoc_toy(request, cat_id, toy_id):
  # Note that you can pass a toy's id instead of the whole object
  Cat.objects.get(id=cat_id).toys.add(toy_id)
  return redirect('detail', cat_id=cat_id)

@login_required
def assoc_toy_delete(request, cat_id, toy_id):
  # Note that you can pass a toy's id instead of the whole object
  Cat.objects.get(id=cat_id).toys.remove(toy_id)
  return redirect('detail', cat_id=cat_id)

@login_required
def add_photo(request, cat_id):
    # attempt to collect the photo file data
    photo_file = request.FILES.get('photo-file', None)
    # use conditional logic to determine if file is present
    if photo_file:
    # if it's present, we will create a reference to the boto3 client
        s3 = boto3.client('s3')
        # create a unique id for each photo file 
        key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
        #  this will take file: funny_cat.png and slice to 34ft68.png
        # upload the photo file to aws s3
        try: 
        # if successful 
            s3.upload_fileobj(photo_file, BUCKET, key)
            # take the exchage url and save it to the database
            url = f"{S3_BASE_URL}{BUCKET}/{key}"
            # 1) create phot instance with photo model and proved cat_id as foreign key value
            photo = Photo(url=url, cat_id=cat_id)
            # 2) save the photo instance to the database
            photo.save()
        except Exception as error:
            print("Error uploading photo: ", error)
            return redirect('detail', cat_id=cat_id)
    # print an error message
    return redirect('detail', cat_id=cat_id)
    # redirect user to the origin page

    """
    check if the request method is POST =
     we need to create a new user because a form was submitted

     1) use the form data from the request to create a form/model instance from the model form
     2) validate the form to ensure it was completed 
        2.2) if form not valid redirect the user to the signup page with an error message
     3) saving the user object to the database
     4) login the user (creates a session for the logged in user in the database)
     5) redirect the user to the cats index page 
    """
"""
    # else the request method is GET == the user clicked on the signup link
    1) create a blank instance of the model form
    2) provide that form instance to a registration template
    3) render the template so the suser can fill out the form
"""
def signup(request):
    error_message = ''
    if request.method == 'POST':
        # This is how to create a 'user' form object that includes the data from the browser
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # This will add the user to the database
            user = form.save()
            # This is how we log a user in via code
            login(request, user)
            return redirect('index')
        else:
            error_message = 'Invalid Info - Please Try Again'
    # A bad POST or GET request, so render signup.html with an empty form
    form = UserCreationForm()
    context = {'form': form, 'error_message': error_message}
    return render(request, 'registration/signup.html', context)


class CatCreate(LoginRequiredMixin, CreateView):
  model = Cat
  # fields = '__all__'
  fields = ['name', 'breed', 'description', 'age']
  success_url = '/cats/'
  
  # This inherited method is called when a 
  # valid cat form is being submitted
  def form_valid(self, form):
    # Assign the logged in user (self.request.user)
    form.instance.user = self.request.user
    # Let the CreateView do its job as usual
    return super().form_valid(form)

class CatUpdate(LoginRequiredMixin, UpdateView):
  model = Cat
  # Let's disallow the renaming of a cat by excluding the name field!
  fields = ['breed', 'description', 'age']

class CatDelete(LoginRequiredMixin, DeleteView):
  model = Cat
  success_url = '/cats/'

class ToyList(LoginRequiredMixin, ListView):
  model = Toy
  template_name = 'toys/index.html'

class ToyDetail(LoginRequiredMixin, DetailView):
  model = Toy
  template_name = 'toys/detail.html'

class ToyCreate(LoginRequiredMixin, CreateView):
    model = Toy
    fields = ['name', 'color']


class ToyUpdate(LoginRequiredMixin, UpdateView):
    model = Toy
    fields = ['name', 'color']


class ToyDelete(LoginRequiredMixin, DeleteView):
    model = Toy
    success_url = '/toys/'



# ================================================================================================
# from django.shortcuts import render
# from django.http import HttpResponse
# from django.views.generic.edit import CreateView
# from .models import Cat
# from django.views.generic.edit import CreateView, UpdateView, DeleteView
# from .forms import FeedingForm
# from django.shortcuts import render, redirect
# # Create your views here.

# def home(request):
#     """
#     this is where we return a repsonse
#     in most cases we would render a template
#     and we'll need some data for that template
#     """
#     # return HttpResponse('<h1>Hello /ᐠ｡‸｡ᐟ\ﾉ</h1>')
#     return render(request, 'home.html')

# def about(request):
#     return render(request, 'about.html')

# ============================THIS NEEDS TO STAY COMMENTED OUT====================================
# This is just seed data until we connect to our database👇🏻
# Add the Cat class & list and view function below the imports
# class Cat:  # Note that parens are optional if not inheriting from another class
#   def __init__(self, name, breed, description, age):
#     self.name = name
#     self.breed = breed
#     self.description = description
#     self.age = age

# cats = [
#   Cat('Lolo', 'tabby', 'foul little demon', 3),
#   Cat('Sachi', 'tortoise shell', 'diluted tortoise shell', 0),
#   Cat('Raven', 'black tripod', '3 legged cat', 4),
#   Cat('Slayer', 'sphinx', 'hairless', 3 )
# ]
# ================================================================================================

# def cats_index(request):
#     cats = Cat.objects.all()
#     return render(request, 'cats/index.html', { 'cats': cats })

  
# def cats_detail(request, cat_id):
#     cat = Cat.objects.get(id=cat_id)
#     feeding_form = FeedingForm()
#     return render(request, 'cats/detail.html', { 'cat' : cat, 'feeding_form': feeding_form })

# class CatCreate(CreateView):
#     model = Cat
#     fields = '__all__'
#     success_url = '/cats/'

# class CatUpdate(UpdateView):
#     model = Cat
#     fields = ['breed', 'description', 'age']

# class CatDelete(DeleteView):
#     model = Cat
#     success_url = '/cats/'

# def add_feeding(request, cat_id):
#     form = FeedingForm(request.POST)
#     if form.is_valid():
#         new_feeding = form.save(commit=False)
#         new_feeding.cat_id = cat_id
#         new_feeding.save()
#     return redirect('detail', cat_id=cat_id)

