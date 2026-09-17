document.addEventListener('alpine:init', () => {
    // Category Form Component (supports Create and Edit)
    Alpine.data('categoryForm', (initialData = {}) => ({
        name: initialData.name || '',
        slug: initialData.slug || '',
        autoSlug: !initialData.slug,
        imagePreview: initialData.imageUrl || null,

        generateSlug() {
            if (this.autoSlug) {
                this.slug = this.name
                    .toLowerCase()
                    .trim()
                    .replace(/[^\w\s-]/g, '')
                    .replace(/[\s_-]+/g, '-')
                    .replace(/^-+|-+$/g, '');
            }
        },

        handleImageChange(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    this.imagePreview = e.target.result;
                };
                reader.readAsDataURL(file);
            }
        }
    }));
});
