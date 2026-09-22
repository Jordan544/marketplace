from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from .validators import validate_image_extension_and_size

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to="profiles/", default="profiles/default.png", blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    age = models.PositiveIntegerField(validators=[MinValueValidator(18), MaxValueValidator(100)], null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    location = models.CharField(max_length=100, blank=True, help_text="e.g. Hostels, Eastern Campus")
    is_seller = models.BooleanField(default=False, help_text="Check this if you want to post listings/products.")

    def __str__(self):
      return f"{self.user.username}'s Profile"

# Automatic Profile Creation Signal
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class Category(models.Model):
  name = models.CharField(max_length=50, unique=True)
  slug = models.SlugField(max_length=50, unique=True)

  class Meta:
    verbose_name_plural = "categories"
  
  def __str__(self):
    return self.name

class Listing(models.Model):
  LISTING_TYPES = (
    ('item', 'Item for Sale/Rent'),
    ('service', 'Service offered'),
  )
  CONDITIONS = (
    ('new', 'Brand New'),
    ('like_new', 'Like New'),
    ('used', 'Fair / Used'),
    ('na', 'Not Applicable (Services)'),
  )
  owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
  category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='listings')

  title = models.CharField(max_length=150)
  description = models.TextField()
  price = models.DecimalField(max_digits=10, decimal_places=2)
  listing_type = models.CharField(max_length=10, choices=LISTING_TYPES, default='item')
  condition = models.CharField(max_length=10, choices=CONDITIONS, default='used')
  image = models.ImageField(upload_to='listings/', validators=[validate_image_extension_and_size], blank=True, null=True)

  is_available = models.BooleanField(default=True)
  created_at = models.DateTimeField(auto_now_add=True)
  updated_at = models.DateTimeField(auto_now=True)

  class Meta:
    ordering = ['-created_at']
  
  def __str__(self):
    return self.title

# Automatic Listing Notification Signal
@receiver(post_save, sender=Listing)
def create_listing_notification(sender, instance, created, **kwargs):
    if created:
        other_users = User.objects.exclude(pk=instance.owner.pk)
        notifications = [
            Notification(
                recipient=user,
                sender=instance.owner,
                listing=instance,
                message=f"{instance.owner.username} posted a new item: {instance.title}"
            )
            for user in other_users
        ]
        Notification.objects.bulk_create(notifications)

class ListingImage(models.Model):
  listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
  image = models.ImageField(upload_to='listings/', validators=[validate_image_extension_and_size])
  caption = models.CharField(max_length=100, blank=True)

  def __str__(self):
    return f"Image for {self.listing.title}"

class Inquiry(models.Model):
  listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='inquiries')
  sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_inquiries')
  receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_inquiries')

  message = models.TextField()
  contact_email = models.EmailField()
  contact_phone = models.CharField(max_length=20, blank=True)

  created_at = models.DateTimeField(auto_now_add=True)
  is_read = models.BooleanField(default=False)

  class Meta:
    verbose_name_plural = 'Inquiries'
    ordering = ['-created_at']

  def __str__(self):
    return f"Inquiry on '{self.listing.title}' by {self.sender.username}"

class Review(models.Model):
  target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
  author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_written')

  rating = models.PositiveSmallIntegerField(
    validators = [MinValueValidator(1), MaxValueValidator(5)]
  )
  comment = models.TextField()
  created_at = models.DateTimeField(auto_now_add=True)

  def __str__(self):
    return f"Review for {self.target_user.username} ({self.rating}/5)"

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')
  
    def __str__(self):
        return f"{self.user.username} saved {self.listing.title}"

class Notification(models.Model):
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message}"