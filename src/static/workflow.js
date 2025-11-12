/**
 * Workflow Kanban Board - JavaScript
 *
 * Handles drag-and-drop, modal interactions, and AJAX operations
 */

// Global state
let draggedElement = null;
let draggedProcessId = null;
let draggedCurrentState = null;

// ========== Drag and Drop Handlers ==========

function handleDragStart(event) {
    draggedElement = event.target;
    draggedProcessId = event.target.dataset.processId;
    draggedCurrentState = event.target.dataset.currentState;

    event.target.classList.add('dragging');
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/html', event.target.innerHTML);
}

function handleDragEnd(event) {
    event.target.classList.remove('dragging');
    draggedElement = null;
}

function handleDragOver(event) {
    if (event.preventDefault) {
        event.preventDefault();
    }
    event.dataTransfer.dropEffect = 'move';
    return false;
}

function handleDragEnter(event) {
    if (event.target.classList.contains('column-body')) {
        event.target.classList.add('drag-over');
    }
}

function handleDragLeave(event) {
    if (event.target.classList.contains('column-body')) {
        event.target.classList.remove('drag-over');
    }
}

function handleDrop(event) {
    if (event.stopPropagation) {
        event.stopPropagation();
    }

    const dropTarget = event.target.closest('.column-body');
    if (!dropTarget) return false;

    dropTarget.classList.remove('drag-over');

    const newState = dropTarget.dataset.state;

    // Don't process if dropped in same column
    if (newState === draggedCurrentState) {
        return false;
    }

    // Check if transition is allowed
    checkAndExecuteTransition(draggedProcessId, draggedCurrentState, newState);

    return false;
}

// ========== Transition Logic ==========

async function checkAndExecuteTransition(processId, fromState, toState) {
    try {
        // First, check if transition is allowed
        const checkResponse = await fetch(`/api/workflow/check_transition`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                process_id: processId,
                from_state: fromState,
                to_state: toState
            })
        });

        const checkResult = await checkResponse.json();

        // NEW PHILOSOPHY: Check if transition is explicitly BLOCKED
        if (!checkResult.allowed) {
            // Show clear blocking message
            const errorMsg = checkResult.error || `Transição bloqueada: ${fromState} → ${toState}`;
            showBlockedTransitionModal(fromState, toState, errorMsg);
            return;
        }

        // Check if transition has WARNING (abnormal flow)
        if (checkResult.warning) {
            const shouldContinue = await promptForWarning(
                fromState,
                toState,
                checkResult.warning
            );

            if (!shouldContinue.confirmed) {
                showToast('Transição cancelada', 'warning');
                return;
            }

            // Execute transition with justification if provided
            executeTransition(processId, toState, 'manual', shouldContinue.justification);
            return;
        }

        // Check prerequisites (for recommended transitions)
        if (checkResult.prerequisites && checkResult.prerequisites.length > 0) {
            const hasFailures = checkResult.prerequisites.some(p => !p.satisfied);

            if (hasFailures) {
                // Show warning and ask for justification
                const justification = await promptForJustification(checkResult.prerequisites);

                if (!justification) {
                    showToast('Transição cancelada', 'warning');
                    return;
                }

                // Execute forced transition
                executeTransition(processId, toState, 'manual', justification);
                return;
            }
        }

        // Execute normal transition
        executeTransition(processId, toState, 'manual');

    } catch (error) {
        console.error('Error checking transition:', error);
        showToast('Erro ao verificar transição', 'error');
    }
}

async function executeTransition(processId, newState, transitionType = 'manual', justification = null) {
    try {
        const response = await fetch(`/api/workflow/transition`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                process_id: processId,
                new_state: newState,
                transition_type: transitionType,
                justification: justification
            })
        });

        const result = await response.json();

        if (result.success) {
            showToast('Transição realizada com sucesso', 'success');
            // Reload board to reflect changes
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            showToast(`Erro: ${result.error}`, 'error');
        }

    } catch (error) {
        console.error('Error executing transition:', error);
        showToast('Erro ao executar transição', 'error');
    }
}

function showBlockedTransitionModal(fromState, toState, reason) {
    const modalHtml = `
        <div class="warning-modal-overlay" id="blockedModal">
            <div class="warning-modal blocked">
                <div class="warning-header blocked">
                    <i class="fas fa-ban"></i>
                    <h3>Transição Bloqueada</h3>
                </div>
                <div class="warning-body">
                    <p class="transition-info">
                        <strong>${fromState}</strong> → <strong>${toState}</strong>
                    </p>
                    <p class="warning-message">${reason}</p>
                    <p class="warning-note">
                        <i class="fas fa-info-circle"></i>
                        Esta transição não é permitida devido a regras de negócio.
                    </p>
                </div>
                <div class="warning-actions">
                    <button class="btn btn-primary" onclick="closeBlockedModal()">Entendido</button>
                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function closeBlockedModal() {
    const modal = document.getElementById('blockedModal');
    if (modal) {
        modal.remove();
    }
}

async function promptForWarning(fromState, toState, warningInfo) {
    return new Promise((resolve) => {
        const requireJustification = warningInfo.require_justification;
        const severity = warningInfo.severity || 'medium';
        const message = warningInfo.message || 'Esta é uma transição anormal.';

        const justificationField = requireJustification ? `
            <div class="form-group">
                <label for="warningJustification">
                    <strong>Justificativa ${requireJustification ? '(obrigatória)' : '(opcional)'}:</strong>
                </label>
                <textarea
                    id="warningJustification"
                    class="form-control"
                    rows="3"
                    placeholder="Descreva o motivo desta transição anormal..."
                    ${requireJustification ? 'required' : ''}
                ></textarea>
            </div>
        ` : '';

        const modalHtml = `
            <div class="warning-modal-overlay" id="warningModal">
                <div class="warning-modal ${severity}">
                    <div class="warning-header ${severity}">
                        <i class="fas fa-exclamation-triangle"></i>
                        <h3>Transição Anormal Detectada</h3>
                    </div>
                    <div class="warning-body">
                        <p class="transition-info">
                            <strong>${fromState}</strong> → <strong>${toState}</strong>
                        </p>
                        <p class="warning-message">${message}</p>
                        <p class="warning-note">
                            <i class="fas fa-info-circle"></i>
                            Esta transição não faz parte do fluxo recomendado.
                        </p>
                        ${justificationField}
                    </div>
                    <div class="warning-actions">
                        <button class="btn btn-secondary" onclick="cancelWarning()">Cancelar</button>
                        <button class="btn btn-warning" onclick="confirmWarning(${requireJustification})">Continuar Mesmo Assim</button>
                    </div>
                </div>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // Store resolve function globally for button handlers
        window.warningResolve = resolve;
    });
}

function cancelWarning() {
    const modal = document.getElementById('warningModal');
    if (modal) {
        modal.remove();
    }
    if (window.warningResolve) {
        window.warningResolve({ confirmed: false, justification: null });
        delete window.warningResolve;
    }
}

function confirmWarning(requireJustification) {
    let justification = null;

    if (requireJustification) {
        const textarea = document.getElementById('warningJustification');
        justification = textarea ? textarea.value.trim() : '';

        if (!justification) {
            showToast('Justificativa obrigatória para esta transição', 'error');
            return;
        }
    } else {
        const textarea = document.getElementById('warningJustification');
        justification = textarea ? textarea.value.trim() : null;
    }

    const modal = document.getElementById('warningModal');
    if (modal) {
        modal.remove();
    }

    if (window.warningResolve) {
        window.warningResolve({ confirmed: true, justification: justification });
        delete window.warningResolve;
    }
}

async function promptForJustification(prerequisites) {
    const failedPrereqs = prerequisites.filter(p => !p.satisfied);

    let message = 'Alguns pré-requisitos não foram atendidos:\n\n';
    failedPrereqs.forEach(p => {
        message += `• ${p.message}\n`;
    });
    message += '\nDeseja continuar mesmo assim? Por favor, justifique:';

    const justification = prompt(message);
    return justification;
}

// ========== Board Actions ==========

function refreshBoard() {
    location.reload();
}

async function showAnalytics() {
    const modal = document.getElementById('analyticsModal');
    const body = document.getElementById('analyticsBody');

    body.innerHTML = '<div class="spinner"></div>';
    modal.style.display = 'flex';

    try {
        const kanbanId = getKanbanIdFromUrl();
        const response = await fetch(`/api/workflow/analytics/${kanbanId}`);
        const data = await response.json();

        body.innerHTML = renderAnalytics(data);

    } catch (error) {
        console.error('Error loading analytics:', error);
        body.innerHTML = '<p>Erro ao carregar analytics</p>';
    }
}

function closeAnalyticsModal() {
    document.getElementById('analyticsModal').style.display = 'none';
}

function renderAnalytics(data) {
    let html = '<div class="process-details">';

    // Total processes
    html += `
        <div class="detail-section">
            <h3>Resumo Geral</h3>
            <div class="detail-row">
                <span class="detail-label">Total de Processos:</span>
                <span class="detail-value">${data.total_processes}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Média de Transições:</span>
                <span class="detail-value">${data.avg_transitions_per_process}</span>
            </div>
        </div>
    `;

    // By state
    html += `
        <div class="detail-section">
            <h3>Processos por Estado</h3>
    `;
    for (const [state, count] of Object.entries(data.by_state)) {
        html += `
            <div class="detail-row">
                <span class="detail-label">${state}:</span>
                <span class="detail-value">${count}</span>
            </div>
        `;
    }
    html += '</div>';

    // By transition type
    if (Object.keys(data.by_transition_type).length > 0) {
        html += `
            <div class="detail-section">
                <h3>Transições por Tipo</h3>
        `;
        for (const [type, count] of Object.entries(data.by_transition_type)) {
            html += `
                <div class="detail-row">
                    <span class="detail-label">${type}:</span>
                    <span class="detail-value">${count}</span>
                </div>
            `;
        }
        html += '</div>';
    }

    html += '</div>';
    return html;
}

// ========== Process Actions ==========

async function viewProcess(processId) {
    const modal = document.getElementById('processModal');
    const title = document.getElementById('modalTitle');
    const body = document.getElementById('modalBody');

    title.textContent = `Processo: ${processId}`;
    body.innerHTML = '<div class="spinner"></div>';
    modal.style.display = 'flex';

    try {
        const response = await fetch(`/api/workflow/process/${processId}`);
        const process = await response.json();

        body.innerHTML = renderProcessDetails(process);

    } catch (error) {
        console.error('Error loading process:', error);
        body.innerHTML = '<p>Erro ao carregar processo</p>';
    }
}

function editProcess(processId) {
    // Navigate to source form edit page
    // This requires knowing the source form and record index
    fetch(`/api/workflow/process/${processId}`)
        .then(response => response.json())
        .then(process => {
            if (process.source_form && process.source_record_idx >= 0) {
                window.location.href = `/${process.source_form}/edit/${process.source_record_idx}`;
            } else {
                showToast('Não é possível editar este processo', 'warning');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Erro ao carregar processo', 'error');
        });
}

function closeModal() {
    document.getElementById('processModal').style.display = 'none';
}

function renderProcessDetails(process) {
    let html = '<div class="process-details">';

    // Basic info
    html += `
        <div class="detail-section">
            <h3>Informações Básicas</h3>
            <div class="detail-row">
                <span class="detail-label">ID do Processo:</span>
                <span class="detail-value">${process.process_id}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Kanban:</span>
                <span class="detail-value">${process.kanban_id}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Estado Atual:</span>
                <span class="detail-value">${process.current_state}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Criado em:</span>
                <span class="detail-value">${formatDateTime(process.created_at)}</span>
            </div>
            <div class="detail-row">
                <span class="detail-label">Atualizado em:</span>
                <span class="detail-value">${formatDateTime(process.updated_at)}</span>
            </div>
        </div>
    `;

    // Field values
    if (process.field_values && Object.keys(process.field_values).length > 0) {
        html += `
            <div class="detail-section">
                <h3>Valores dos Campos</h3>
        `;
        for (const [key, value] of Object.entries(process.field_values)) {
            html += `
                <div class="detail-row">
                    <span class="detail-label">${key}:</span>
                    <span class="detail-value">${value}</span>
                </div>
            `;
        }
        html += '</div>';
    }

    // History
    if (process.history && process.history.length > 0) {
        html += `
            <div class="detail-section">
                <h3>Histórico de Transições</h3>
                <div class="history-timeline">
        `;

        process.history.forEach(entry => {
            html += `
                <div class="timeline-item">
                    <div class="timeline-dot"></div>
                    <div class="timeline-content">
                        <div class="timeline-header">
                            <span class="timeline-transition">${entry.from_state} → ${entry.to_state}</span>
                            <span class="timeline-date">${formatDateTime(entry.timestamp)}</span>
                        </div>
                        <div class="timeline-meta">
                            Tipo: ${entry.type} | Usuário: ${entry.user || 'system'}
                        </div>
                        ${entry.justification ? `<div class="timeline-meta">Justificativa: ${entry.justification}</div>` : ''}
                    </div>
                </div>
            `;
        });

        html += '</div></div>';
    }

    html += '</div>';
    return html;
}

// ========== Utility Functions ==========

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.style.display = 'block';

    setTimeout(() => {
        toast.style.display = 'none';
    }, 3000);
}

function formatDateTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString('pt-BR');
}

function getKanbanIdFromUrl() {
    const pathParts = window.location.pathname.split('/');
    return pathParts[pathParts.length - 1];
}

// ========== Initialize Drag and Drop ==========

document.addEventListener('DOMContentLoaded', function() {
    // Add event listeners to all column bodies
    const columns = document.querySelectorAll('.column-body');
    columns.forEach(column => {
        column.addEventListener('dragover', handleDragOver, false);
        column.addEventListener('dragenter', handleDragEnter, false);
        column.addEventListener('dragleave', handleDragLeave, false);
        column.addEventListener('drop', handleDrop, false);
    });

    // Close modals when clicking outside
    window.onclick = function(event) {
        const processModal = document.getElementById('processModal');
        const analyticsModal = document.getElementById('analyticsModal');

        if (event.target === processModal) {
            closeModal();
        }
        if (event.target === analyticsModal) {
            closeAnalyticsModal();
        }
    };
});
