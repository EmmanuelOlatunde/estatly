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
            self.stdout.write(f"Repairing document {doc.id} (status={doc.status})")
            try:
                # Force clear the file reference regardless of what's stored
                if doc.file:
                    try:
                        doc.file.delete(save=False)
                    except Exception:
                        pass
                    doc.file = None

                # Reset to clean state directly — bypass service layer guard
                doc.status = DocumentStatus.PENDING
                doc.error_message = ''
                doc.file_size = None
                doc.generated_at = None
                doc.save(update_fields=['file', 'status', 'error_message', 'file_size', 'generated_at', 'updated_at'])

                # Generate directly
                pdf_content = generate_document_pdf_content(doc)
                services.generate_document_pdf(document=doc, pdf_content=pdf_content)
                self.stdout.write(self.style.SUCCESS(f"  ✓ Done: {doc.id}"))
                count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ✗ Failed: {doc.id} - {e}"))
                try:
                    services.mark_document_generation_failed(
                        document=doc, error_message=str(e)
                    )
                except Exception:
                    pass
                failed += 1

        self.stdout.write(self.style.SUCCESS(f"\nRepaired: {count}, Failed: {failed}"))