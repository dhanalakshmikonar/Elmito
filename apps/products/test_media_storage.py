from io import BytesIO
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import Http404
from django.test import TestCase
from django.urls import reverse
from django.test import RequestFactory
from django.views.static import serve
from PIL import Image

from apps.products.models import Category, Product, ProductImage


class AdminProductImageStorageTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.media_dir.cleanup)
        self.settings_override = self.settings(MEDIA_ROOT=self.media_dir.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        User = get_user_model()
        admin = User.objects.create_superuser(
            username="image-admin",
            email="image-admin@example.com",
            password="test-password-123",
            mobile="9876543210",
            full_name="Image Admin",
        )
        self.client.force_login(admin)
        self.category = Category.objects.create(name="Upload Test Category")

    def test_admin_upload_saves_path_serves_file_and_missing_file_is_404(self):
        image_buffer = BytesIO()
        Image.new("RGB", (1, 1), color=(10, 20, 30)).save(image_buffer, format="PNG")
        image_bytes = image_buffer.getvalue()
        response = self.client.post(
            reverse("admin:products_product_add"),
            data={
                "name": "Admin Upload Test",
                "slug": "admin-upload-test",
                "sku": "UPLOAD-TEST-1",
                "description": "",
                "category": str(self.category.pk),
                "price": "1000.00",
                "discount_price": "",
                "status": Product.Status.ACTIVE,
                "images-TOTAL_FORMS": "1",
                "images-INITIAL_FORMS": "0",
                "images-MIN_NUM_FORMS": "0",
                "images-MAX_NUM_FORMS": "1000",
                "images-0-image": SimpleUploadedFile("test.png", image_bytes, "image/png"),
                "images-0-color": "Black",
                "images-0-alt_text": "Test upload",
                "images-0-is_primary": "on",
                "images-0-position": "0",
                "variants-TOTAL_FORMS": "0",
                "variants-INITIAL_FORMS": "0",
                "variants-MIN_NUM_FORMS": "0",
                "variants-MAX_NUM_FORMS": "1000",
                "_save": "Save",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

        if not Product.objects.filter(sku="UPLOAD-TEST-1").exists():
            errors = response.context["adminform"].form.errors
            inline_errors = [fs.formset.errors for fs in response.context["inline_admin_formsets"]]
            self.fail(f"Admin rejected upload: product={errors}, inlines={inline_errors}")

        product = Product.objects.get(sku="UPLOAD-TEST-1")
        image = ProductImage.objects.get(product=product)
        self.assertTrue(image.image.name.startswith("products/"))
        stored_path = Path(self.media_dir.name, image.image.name)
        self.assertTrue(stored_path.is_file())
        self.assertEqual(image.image.url, f"/media/{image.image.name}")
        product_page = self.client.get(product.get_absolute_url())
        self.assertContains(product_page, f'src="{image.image.url}"')

        rendered = serve(
            RequestFactory().get(image.image.url),
            path=image.image.name,
            document_root=self.media_dir.name,
        )
        self.assertEqual(rendered.status_code, 200)
        self.assertEqual(b"".join(rendered.streaming_content), image_bytes)
        rendered.close()

        stored_path.unlink()
        with self.assertRaises(Http404):
            serve(
                RequestFactory().get(image.image.url),
                path=image.image.name,
                document_root=self.media_dir.name,
            )
        # The database still stores the relative name; it cannot reconstruct the file.
        image.refresh_from_db()
        self.assertEqual(image.image.name, stored_path.relative_to(self.media_dir.name).as_posix())
