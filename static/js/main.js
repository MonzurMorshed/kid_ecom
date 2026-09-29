function specificationsBuilder(initialSpecs = []) {
    return {
        specs: Array.isArray(initialSpecs) && initialSpecs.length > 0 
            ? initialSpecs 
            : (typeof getInitialProductSpecs === 'function' ? getInitialProductSpecs() : []),
        addSpec(label = '', value = '') {
            this.specs.push({ label: label, value: value });
        },
        addPreset(label, defaultValue = '') {
            this.specs.push({ label: label, value: defaultValue });
        },
        removeSpec(index) {
            this.specs.splice(index, 1);
        }
    };
}
window.specificationsBuilder = specificationsBuilder;

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

    // Register with Alpine.data
    Alpine.data('specificationsBuilder', specificationsBuilder);
});
