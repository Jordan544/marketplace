from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.forms import inlineformset_factory
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth import login, authenticate
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required
from .models import Category, Listing, Inquiry
from .forms import CategoryForm

from .models import Listing, ListingImage, Category, Inquiry, Profile, Wishlist, Notification
from .forms import ListingForm, ListingImageForm, InquiryForm, SignUpForm, UserUpdateForm, ProfileUpdateForm

def listing_list(request):
  listings = Listing.objects.filter(is_available=True)
  categories = Category.objects.all()

  query = request.GET.get('q')
  if query:
    listings = listings.filter(
      Q(title__icontains=query) | Q(description__icontains=query)
    )

  category_slug = request.GET.get('category')
  if category_slug:
    listings = listings.filter(category__slug=category_slug)

  seller_query = request.GET.get('seller')
  if seller_query:
    listings = listings.filter(owner__username__icontains=seller_query)

  location_query = request.GET.get('location')
  if location_query:
    listings = listings.filter(owner__profile__campus_location__icontains=location_query)

  sort_by = request.GET.get('sort', 'newest')
  if sort_by == 'oldest':
    listings = listings.order_by('created_at')
  elif sort_by == 'price_low':
    listings = listings.order_by('price')
  elif sort_by == 'price_high':
    listings = listings.order_by('-price')
  else:
    listings = listings.order_by('-created_at')
  
  paginator = Paginator(listings, 6)
  page_number = request.GET.get('page')
  page_obj = paginator.get_page(page_number)

  context = {
    'page_obj': page_obj,
    'categories': categories,
    'selected_category': category_slug,
    'query': query,
    'seller_query': seller_query,
    'location_query': location_query,
    'sort_by': sort_by,
  }
  return render(request, 'consentform/listing_list.html', context)

@ratelimit(key='ip', rate='10/m', method='POST', block=False)
def listing_detail(request, pk):
  if getattr(request, 'limited', False):
    messages.error(request, "Too many inquiry submissions. Please wait a moment before trying again.")
    return redirect('listing_detail', pk=pk)

  listing = get_object_or_404(Listing, pk=pk)

  if request.method == 'POST':
    if not request.user.is_authenticated:
      messages.error(request, "You must be logged in to send an inquiry.")
      return redirect('login')
    
    inquiry_form = InquiryForm(request.POST)
    if inquiry_form.is_valid():
      inquiry = inquiry_form.save(commit=False)
      inquiry.listing = listing
      inquiry.sender = request.user
      inquiry.receiver = listing.owner
      inquiry.save()
      messages.success(request, "Your inquiry has been sent to the owner.")
      return redirect('listing_detail', pk=pk)
  else:
    inquiry_form = InquiryForm()

  context = {
    'listing': listing,
    'inquiry_form': inquiry_form,
  }
  return render(request, 'consentform/listing_detail.html', context)

@login_required
def listing_create(request):
  if not hasattr(request.user, 'profile') or not request.user.profile.is_seller:
    messages.error(request, "Only registered seller accounts can create listings. Update your profile to become a seller.")
    return redirect('profile_edit')

  ImageFormSet = inlineformset_factory(
    Listing, ListingImage, form=ListingImageForm, extra=3, can_delete=False
  )
  if request.method == 'POST':
    form = ListingForm(request.POST, request.FILES)
    formset = ImageFormSet(request.POST, request.FILES)

    if form.is_valid() and formset.is_valid():
      listing = form.save(commit=False)
      listing.owner = request.user
      listing.save()

      formset.instance = listing
      formset.save()

      messages.success(request, "Listing created successfully!")
      return redirect('listing_detail', pk=listing.pk)
  else:
    form = ListingForm()
    formset = ImageFormSet()

  context = {
    'form': form,
    'formset': formset,
    'title': 'Create New Listing',
  }
  return render(request, 'consentform/listing_form.html', context)

@login_required
def listing_update(request, pk):
  listing = get_object_or_404(Listing, pk=pk)

  if listing.owner != request.user:
    messages.error(request, "You are not authorized to edit this listing.")
    return redirect('listing_detail', pk=listing.pk)
  
  ImageFormSet = inlineformset_factory(
    Listing, ListingImage, form=ListingImageForm, extra=1, can_delete=True
  )
  if request.method == 'POST':
    form = ListingForm(request.POST, request.FILES, instance=listing)
    formset = ImageFormSet(request.POST, request.FILES, instance=listing)

    if form.is_valid() and formset.is_valid():
      form.save()
      formset.save()
      messages.success(request, "Listing updated successfully!")
      return redirect('listing_detail', pk=listing.pk)
  else:
    form = ListingForm(instance=listing)
    formset = ImageFormSet(instance=listing)

  context = {
    'form': form,
    'formset': formset,
    'title': 'Edit Listing',
  }
  return render(request, 'consentform/listing_form.html', context)

@login_required
def listing_delete(request, pk):
  listing = get_object_or_404(Listing, pk=pk)

  if listing.owner != request.user:
    messages.error(request, "You are not authorized to delete this listing.")
    return redirect('listing_detail', pk=listing.pk)
  
  if request.method == 'POST':
    listing.delete()
    messages.success(request, "Listing deleted successfully.")
    return redirect('listing_list')
  
  context = {
    'listing': listing
  }
  return render(request, 'consentform/listing_delete.html', context)

@login_required
def toggle_inquiry_read(request, pk):
  inquiry = get_object_or_404(Inquiry, pk=pk, receiver=request.user)
  inquiry.is_read = not inquiry.is_read
  inquiry.save()
  status_label = "read" if inquiry.is_read else "unread"
  messages.success(request, f"Inquiry marked as {status_label}.")
  return redirect('dashboard')

@login_required
def delete_inquiry(request, pk):
  inquiry = get_object_or_404(Inquiry, pk=pk)
  if request.user == inquiry.sender or request.user == inquiry.receiver:
    inquiry.delete()
    messages.success(request, "Inquiry deleted successfully.")
  else:
    messages.error(request, "You are not authorized to delete this inquiry.")
  return redirect('dashboard')

@ratelimit(key='ip', rate='5/m', method='POST', block=False)
def signup_view(request):
    if getattr(request, 'limited', False):
        messages.error(request, "Too many signup attempts from this IP address. Please try again later.")
        return redirect('signup')

    if request.user.is_authenticated:
        return redirect('listing_list')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to Campus Marketplace, {user.username}!")
            return redirect('listing_list')
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})

@login_required
def profile_edit(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            profile = p_form.save(commit=False)
            profile.is_seller = True if request.POST.get('is_seller') == 'on' else False
            profile.save()
            
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('dashboard')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form, 
        'p_form': p_form
    }
    return render(request, 'consentform/profile_edit.html', context)

@login_required
def dashboard(request):
  received_inquiries = Inquiry.objects.filter(
    receiver=request.user
  ).select_related('listing', 'sender')

  sent_inquiries = Inquiry.objects.filter(
    sender=request.user
  ).select_related('listing', 'receiver')

  unread_count = received_inquiries.filter(is_read=False).count()
  all_listings = Listing.objects.filter(is_available=True)

  context = {
    'received_inquiries': received_inquiries,
    'sent_inquiries': sent_inquiries,
    'unread_count': unread_count,
    'all_listings': all_listings,
  }
  return render(request, 'consentform/dashboard.html', context)

@login_required
def toggle_wishlist(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, listing=listing)
    
    if not created:
        wishlist_item.delete()
        messages.success(request, "Removed from your saved wishlist.")
    else:
        messages.success(request, "Added to your saved wishlist!")
        
    return redirect('listing_detail', pk=pk)

@login_required
def notification_list(request):
    notifications = request.user.notifications.all()
    unread_count = notifications.filter(is_read=False).count()
    return render(request, 'consentform/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })

@login_required
def mark_notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save()
    if notification.listing:
        return redirect('listing_detail', pk=notification.listing.pk)
    return redirect('notification_list')

@login_required
def notification_list(request):
    filter_type = request.GET.get('filter', 'all')
    notifications = request.user.notifications.all()
    
    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)
        
    unread_count = request.user.notifications.filter(is_read=False).count()
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
        'current_filter': filter_type,
    }
    return render(request, 'consentform/notifications.html', context)

@login_required
def mark_all_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, "All notifications marked as read.")
    return redirect('notification_list')

def admin_login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('manage_categories') # Or your main admin dashboard route

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            messages.success(request, f"Welcome back, Administrator {user.username}!")
            return redirect('manage_categories')
        else:
            messages.error(request, "Invalid credentials or you do not have administrator privileges.")
            
    return render(request, 'consentform/admin_login.html')


@staff_member_required
def manage_categories(request):
    categories = Category.objects.all()
    users = User.objects.all().select_related('profile')
    listings = Listing.objects.all()
    

    total_users_count = users.count()
    total_listings_count = listings.count()
    total_categories_count = categories.count()

    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category added successfully!")
            return redirect('manage_categories')
    else:
        form = CategoryForm()

    context = {
        'categories': categories,
        'users': users,
        'listings': listings,
        'form': form,
        'total_users_count': total_users_count,
        'total_listings_count': total_listings_count,
        'total_categories_count': total_categories_count,
    }
    return render(request, 'consentform/manage_categories.html', context)

@staff_member_required
def admin_delete_user(request, user_id):
    user_to_delete = get_object_or_404(User, pk=user_id)
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete your own active admin account.")
    else:
        user_to_delete.delete()
        messages.success(request, "User deleted successfully.")
    return redirect('manage_categories')

@staff_member_required
def admin_delete_listing(request, listing_id):
    listing_to_delete = get_object_or_404(Listing, pk=listing_id)
    listing_to_delete.delete()
    messages.success(request, "Listing deleted successfully by administrator.")
    return redirect('manage_categories')