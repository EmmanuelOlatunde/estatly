from django.core.management.base import BaseCommand
from documents.models import Document, DocumentStatus
from documents import services
from documents.generators import generate_document_pdf_content


class Command(BaseCommand):
    help = "Repair missing PDF files and regenerate them"

    def handle(self, *args, **kwargs):
        count = 0
        failed = 0

        docs = Document.objects.filter(is_deleted=False).exclude(
            status=DocumentStatus.COMPLETED
        )

        for doc in docs.iterator():
            self.stdout.write(f"Repairing {doc.id} (status={doc.status})")
            try:
                # Use raw SQL update to clear file field — bypasses signals and service guards
                Document.objects.filter(pk=doc.pk).update(
                    file='',
                    status=DocumentStatus.PENDING,
                    error_message='',
                    file_size=None,
                    generated_at=None,
                )

                # Refresh from DB so doc now has clean state
                doc.refresh_from_db()

                # Generate PDF directly
                pdf_content = generate_document_pdf_content(doc)
                services.generate_document_pdf(document=doc, pdf_content=pdf_content)

                self.stdout.write(self.style.SUCCESS(f"  ✓ Done: {doc.id}"))
                count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Failed: {doc.id} - {e}"))
                Document.objects.filter(pk=doc.pk).update(
                    status=DocumentStatus.FAILED,
                    error_message=str(e)[:500],
                )
                failed += 1

        self.stdout.write(self.style.SUCCESS(f"\nRepaired: {count}, Failed: {failed}"))