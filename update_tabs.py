import re

with open('app/templates/admin/modules.html', 'r') as f:
    content = f.read()

# 1. Add Tabs Header before the form
tabs_header = """
    <!-- Tabs Header -->
    <div class="flex flex-wrap gap-0 mt-6 relative z-10 -mb-[2px] overflow-x-auto">
        <button type="button" class="tab-btn active px-4 sm:px-6 py-3 border-2 border-black border-b-0 bg-white font-bold uppercase text-black whitespace-nowrap focus:outline-none" data-target="tab-core">Módulos</button>
        <button type="button" class="tab-btn px-4 sm:px-6 py-3 border-2 border-black border-b-0 border-l-0 bg-gray-200 font-bold uppercase text-gray-600 hover:bg-gray-100 transition-colors whitespace-nowrap focus:outline-none" data-target="tab-ai">I.A.</button>
        <button type="button" class="tab-btn px-4 sm:px-6 py-3 border-2 border-black border-b-0 border-l-0 bg-gray-200 font-bold uppercase text-gray-600 hover:bg-gray-100 transition-colors whitespace-nowrap focus:outline-none" data-target="tab-smtp">SMTP & E-mail</button>
        <button type="button" class="tab-btn px-4 sm:px-6 py-3 border-2 border-black border-b-0 border-l-0 bg-gray-200 font-bold uppercase text-gray-600 hover:bg-gray-100 transition-colors whitespace-nowrap focus:outline-none" data-target="tab-rbac">Permissões</button>
    </div>

    <!-- Modules Form -->
    <form action="/admin/modulos" method="POST" class="bg-white border-2 border-black p-6 sm:p-8 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] relative z-0">
        
        <!-- TAB: MÓDULOS -->
        <div id="tab-core" class="tab-content block space-y-6">
"""
content = content.replace('    <!-- Modules Form -->\n    <form action="/admin/modulos" method="POST" class="bg-white border-2 border-black p-8 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] space-y-8">\n        <div class="space-y-6">', tabs_header)

# If it didn't find the exact match from earlier, fallback to regex
if tabs_header not in content:
    content = re.sub(
        r'<!-- Modules Form -->\s*<form action="/admin/modulos" method="POST"[^>]+>\s*<div class="space-y-6">',
        tabs_header,
        content
    )
    # also remove the injected tabs header from previous attempt if it's there
    content = re.sub(r'<!-- Tabs Header -->.*?<!-- Modules Form -->', '<!-- Modules Form -->', content, flags=re.DOTALL)
    content = re.sub(
        r'<!-- Modules Form -->\s*<form action="/admin/modulos" method="POST"[^>]+>\s*<!-- TAB: MÓDULOS CORE -->\s*<div id="tab-core" class="tab-content block space-y-6">',
        tabs_header,
        content
    )


# 2. Extract AI section and put it in tab-ai
ai_start = content.find('<div class="border-2 border-gray-200 p-6 hover:border-black transition-colors bg-gray-50">\n                <div class="flex items-start justify-between gap-4">\n                    <div class="space-y-2 w-full">\n                        <div class="flex items-center justify-between">\n                            <div class="flex items-center gap-3">\n                                <span class="font-bold text-lg text-black uppercase tracking-tight">Assistente de Inteligência Artificial</span>')
ai_end = content.find('<!-- Outros módulos futuros podem ser listados aqui -->')
if ai_start != -1 and ai_end != -1:
    ai_block = content[ai_start:ai_end]
    content = content[:ai_start] + content[ai_end:]

    # 3. Close tab-core, insert tab-ai before SMTP
    smtp_start = content.find('<!-- Seção SMTP (Envio de E-mails) -->')
    tab_ai_wrapper = f"""
        </div> <!-- End tab-core -->
        
        <!-- TAB: IA -->
        <div id="tab-ai" class="tab-content hidden space-y-6">
            {ai_block.replace('<div class="border-2 border-gray-200 p-6 hover:border-black transition-colors bg-gray-50">', '<div class="border-2 border-black bg-white p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)]">')}
        </div>
        
"""
    content = content[:smtp_start] + tab_ai_wrapper + content[smtp_start:]

# 4. Wrap SMTP in tab-smtp
smtp_start = content.find('<!-- Seção SMTP (Envio de E-mails) -->')
smtp_end = content.find('<!-- Seção de Acessos por Menu (Matriz de Permissões) -->')
if smtp_start != -1 and smtp_end != -1:
    smtp_block = content[smtp_start:smtp_end]
    content = content[:smtp_start] + f"""
        <!-- TAB: SMTP -->
        <div id="tab-smtp" class="tab-content hidden space-y-6">
            {smtp_block.replace('<div class="border-2 border-black bg-white p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] space-y-4 mb-6 transition-all">', '<div class="border-2 border-black bg-white p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)] space-y-4">')}
        </div>
""" + content[smtp_end:]

# 5. Wrap RBAC in tab-rbac
rbac_start = content.find('<!-- Seção de Acessos por Menu (Matriz de Permissões) -->')
rbac_end = content.find('<div class="pt-4 border-t-2 border-black flex items-center justify-end gap-4">')
if rbac_start != -1 and rbac_end != -1:
    rbac_block = content[rbac_start:rbac_end]
    content = content[:rbac_start] + f"""
        <!-- TAB: RBAC -->
        <div id="tab-rbac" class="tab-content hidden space-y-6">
            {rbac_block.replace('<div class="border-2 border-black bg-white p-6 shadow-[8px_8px_0px_0px_rgba(0,0,0,0.1)] space-y-4">', '<div class="border-2 border-black bg-white p-6 shadow-[4px_4px_0px_0px_rgba(0,0,0,0.1)] space-y-4">')}
        </div>
""" + content[rbac_end:]

# 6. Add JS for Tabs
tabs_js = """
// Script para controle de abas
document.addEventListener('DOMContentLoaded', function() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active de todos
            tabBtns.forEach(b => {
                b.classList.remove('active', 'bg-white', 'text-black');
                b.classList.add('bg-gray-200', 'text-gray-600');
            });
            tabContents.forEach(c => {
                c.classList.remove('block');
                c.classList.add('hidden');
            });

            // Ativa o clicado
            btn.classList.add('active', 'bg-white', 'text-black');
            btn.classList.remove('bg-gray-200', 'text-gray-600');
            
            const targetId = btn.getAttribute('data-target');
            document.getElementById(targetId).classList.remove('hidden');
            document.getElementById(targetId).classList.add('block');
        });
    });
});
"""

if "Script para controle de abas" not in content:
    content = content.replace('</script>\n{% endblock %}', tabs_js + '\n</script>\n{% endblock %}')

# Fix extra closing divs if there are any trailing before TAB: SMTP
content = content.replace('        </div>\n        </div>\n\n        <!-- TAB: SMTP -->', '        <!-- TAB: SMTP -->')
content = content.replace('        </div>\n        </div>\n        </div>\n\n        <!-- TAB: SMTP -->', '        <!-- TAB: SMTP -->')

with open('app/templates/admin/modules.html', 'w') as f:
    f.write(content)
print("Updated successfully")
