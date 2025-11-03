/**
 * Admin JavaScript - Área Administrativa Workflow-Kanban
 * Lógica de interação da interface administrativa
 */

// ========== UTILITÁRIOS ==========

/**
 * Mostra mensagem de toast
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Confirmação de exclusão
 */
function confirmDelete(message = 'Tem certeza que deseja excluir?') {
    return confirm(message);
}

/**
 * Validação de formulário
 */
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;

    const requiredInputs = form.querySelectorAll('[required]');
    let isValid = true;

    requiredInputs.forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = '#e74c3c';
            isValid = false;
        } else {
            input.style.borderColor = '#34495e';
        }
    });

    if (!isValid) {
        showToast('Preencha todos os campos obrigatórios', 'error');
    }

    return isValid;
}

// ========== FILTRO E BUSCA ==========

/**
 * Filtrar lista de kanbans
 */
function filterKanbans(searchTerm) {
    const cards = document.querySelectorAll('.kanban-card');
    const term = searchTerm.toLowerCase();

    cards.forEach(card => {
        const title = card.querySelector('.kanban-card-title')?.textContent.toLowerCase() || '';
        const description = card.querySelector('.kanban-card-description')?.textContent.toLowerCase() || '';
        const id = card.querySelector('.kanban-card-id')?.textContent.toLowerCase() || '';

        if (title.includes(term) || description.includes(term) || id.includes(term)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// ========== NAVEGAÇÃO ==========

/**
 * Voltar para a página anterior
 */
function goBack() {
    window.history.back();
}

/**
 * Redirecionar para URL
 */
function navigateTo(url) {
    window.location.href = url;
}

// ========== MANIPULAÇÃO DE ESTADOS ==========

/**
 * Adicionar estado ao formulário
 */
function addState() {
    const statesContainer = document.getElementById('states-container');
    if (!statesContainer) return;

    const stateCount = statesContainer.children.length;
    const stateHtml = `
        <div class="state-item" data-state-index="${stateCount}">
            <div class="form-group">
                <label>ID do Estado</label>
                <input type="text" name="state_id_${stateCount}" placeholder="ex: em_analise" required>
            </div>
            <div class="form-group">
                <label>Nome do Estado</label>
                <input type="text" name="state_name_${stateCount}" placeholder="ex: Em Análise" required>
            </div>
            <div class="form-group">
                <label>Tipo</label>
                <select name="state_type_${stateCount}">
                    <option value="intermediate">Intermediário</option>
                    <option value="initial">Inicial</option>
                    <option value="final">Final</option>
                </select>
            </div>
            <div class="form-group">
                <label>Cor</label>
                <input type="color" name="state_color_${stateCount}" value="#3498db">
            </div>
            <button type="button" class="btn btn-danger btn-sm" onclick="removeState(${stateCount})">
                <i class="fa fa-trash"></i> Remover
            </button>
        </div>
    `;

    statesContainer.insertAdjacentHTML('beforeend', stateHtml);
}

/**
 * Remover estado do formulário
 */
function removeState(index) {
    const stateItem = document.querySelector(`[data-state-index="${index}"]`);
    if (stateItem && confirmDelete('Remover este estado?')) {
        stateItem.remove();
    }
}

// ========== MANIPULAÇÃO DE TRANSIÇÕES ==========

/**
 * Adicionar transição ao formulário
 */
function addTransition() {
    const transitionsContainer = document.getElementById('transitions-container');
    if (!transitionsContainer) return;

    const transitionCount = transitionsContainer.children.length;
    const transitionHtml = `
        <div class="transition-item" data-transition-index="${transitionCount}">
            <div class="form-group">
                <label>De (Estado Origem)</label>
                <select name="transition_from_${transitionCount}" class="state-select" required>
                    <option value="">Selecione...</option>
                </select>
            </div>
            <div class="form-group">
                <label>Para (Estado Destino)</label>
                <select name="transition_to_${transitionCount}" class="state-select" required>
                    <option value="">Selecione...</option>
                </select>
            </div>
            <div class="form-group">
                <label>Tipo</label>
                <select name="transition_type_${transitionCount}">
                    <option value="recommended">Recomendada</option>
                    <option value="warned">Com Aviso</option>
                    <option value="blocked">Bloqueada</option>
                </select>
            </div>
            <button type="button" class="btn btn-danger btn-sm" onclick="removeTransition(${transitionCount})">
                <i class="fa fa-trash"></i> Remover
            </button>
        </div>
    `;

    transitionsContainer.insertAdjacentHTML('beforeend', transitionHtml);
    updateStateSelects();
}

/**
 * Remover transição do formulário
 */
function removeTransition(index) {
    const transitionItem = document.querySelector(`[data-transition-index="${index}"]`);
    if (transitionItem && confirmDelete('Remover esta transição?')) {
        transitionItem.remove();
    }
}

/**
 * Atualizar selects de estado nas transições
 */
function updateStateSelects() {
    const stateInputs = document.querySelectorAll('[name^="state_id_"]');
    const stateSelects = document.querySelectorAll('.state-select');

    const states = Array.from(stateInputs).map(input => ({
        id: input.value,
        name: document.querySelector(`[name="state_name_${input.name.split('_')[2]}"]`)?.value || input.value
    })).filter(s => s.id);

    stateSelects.forEach(select => {
        const currentValue = select.value;
        select.innerHTML = '<option value="">Selecione...</option>';

        states.forEach(state => {
            const option = document.createElement('option');
            option.value = state.id;
            option.textContent = state.name;
            if (state.id === currentValue) option.selected = true;
            select.appendChild(option);
        });
    });
}

// ========== VINCULAR FORMULÁRIOS ==========

/**
 * Adicionar formulário ao kanban
 */
function addFormMapping(kanbanId, formPath) {
    // Implementar lógica de adicionar mapeamento via AJAX
    fetch(`/admin/workflow/mappings/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kanban_id: kanbanId, form_path: formPath })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Formulário vinculado com sucesso!', 'success');
            location.reload();
        } else {
            showToast(data.error || 'Erro ao vincular formulário', 'error');
        }
    })
    .catch(error => {
        showToast('Erro ao vincular formulário: ' + error.message, 'error');
    });
}

/**
 * Remover formulário do kanban
 */
function removeFormMapping(kanbanId, formPath) {
    if (!confirmDelete('Desvincular este formulário?')) return;

    fetch(`/admin/workflow/mappings/remove`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ kanban_id: kanbanId, form_path: formPath })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Formulário desvinculado com sucesso!', 'success');
            location.reload();
        } else {
            showToast(data.error || 'Erro ao desvincular formulário', 'error');
        }
    })
    .catch(error => {
        showToast('Erro ao desvincular formulário: ' + error.message, 'error');
    });
}

// ========== INICIALIZAÇÃO ==========

document.addEventListener('DOMContentLoaded', function() {
    // Adicionar listeners para inputs de estado (atualizar selects de transição)
    const statesContainer = document.getElementById('states-container');
    if (statesContainer) {
        statesContainer.addEventListener('input', function(e) {
            if (e.target.name && e.target.name.startsWith('state_')) {
                updateStateSelects();
            }
        });
    }

    // Adicionar CSS de animações
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }

        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }

        .state-item, .transition-item {
            background: #2c3e50;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 4px solid #3498db;
        }

        .state-item:hover, .transition-item:hover {
            border-left-color: #27ae60;
        }
    `;
    document.head.appendChild(style);
});

// Expor funções globalmente
window.showToast = showToast;
window.confirmDelete = confirmDelete;
window.validateForm = validateForm;
window.filterKanbans = filterKanbans;
window.goBack = goBack;
window.navigateTo = navigateTo;
window.addState = addState;
window.removeState = removeState;
window.addTransition = addTransition;
window.removeTransition = removeTransition;
window.updateStateSelects = updateStateSelects;
window.addFormMapping = addFormMapping;
window.removeFormMapping = removeFormMapping;
