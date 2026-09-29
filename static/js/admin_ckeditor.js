/**
 * CKEditor 5 initialization for standard Django Admin (/django-admin/)
 */
document.addEventListener('DOMContentLoaded', function () {
    const fields = document.querySelectorAll('#id_description, #id_long_description');
    if (fields.length && window.ClassicEditor) {
        fields.forEach(field => {
            ClassicEditor.create(field, {
                toolbar: [
                    'heading', '|',
                    'bold', 'italic', 'underline', 'strikethrough', '|',
                    'link', 'bulletedList', 'numberedList', 'blockQuote', '|',
                    'insertTable', 'undo', 'redo'
                ]
            })
            .then(editor => {
                editor.model.document.on('change:data', () => {
                    field.value = editor.getData();
                });
                if (field.form) {
                    field.form.addEventListener('submit', () => {
                        field.value = editor.getData();
                    });
                }
            })
            .catch(err => {
                console.error('Django admin CKEditor error:', err);
            });
        });
    }
});
