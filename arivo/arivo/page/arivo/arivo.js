frappe.pages['arivo'].on_page_load = function(wrapper) {
    let page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Arivo Collections',
        single_column: true
    });
    
    $(wrapper).find('.page-content').html(`
        <div id="arivo-root" style="height: calc(100vh - 60px); width: 100%;"></div>
    `);
    
    frappe.require([
        '/assets/arivo/frontend/index.js',
        '/assets/arivo/frontend/index.css'
    ], function() {
        if (window.mountArivo) {
            window.mountArivo(document.getElementById('arivo-root'));
        }
    });
}
