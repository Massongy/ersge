// static/src/js/portal_dossier.js


console.log("Début du script portal_dossier.js");

// Patch pour éviter les ID vides
const originalGetElementById = document.getElementById;
document.getElementById = function(id) {
    if (id === '') {
        console.trace('getElementById appelé avec une chaîne vide');
        return null;
    }
    return originalGetElementById.call(this, id);
};

// =====================================================================
// TABLES DE CORRESPONDANCE RÉDUCTIONS
// =====================================================================
const CHILDREN_MAP = {1: 0.0, 2: 10.0, 3: 20.0, 4: 30.0};
const SENIORITY_MAP = {'5': 0.0, '6': 2.0, '7': 4.0, '8': 6.0, '9': 8.0, '10': 10.0};

// =====================================================================
// UTILITAIRES
// =====================================================================
function setVal(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = (typeof val === 'number') ? val.toFixed(2) : val;
}
function setInner(id, val) {
    const el = document.getElementById(id);
    if (el) el.innerText = (typeof val === 'number') ? val.toFixed(2) : val;
}
function getCheckedVal(root, name) {
    const el = root.querySelector('input[name="' + name + '"]:checked');
    return el ? el.value : null;
}
function getCsrfToken() {
    const token = document.querySelector('input[name="csrf_token"]');
    if (token) return token.value;
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

// =====================================================================
// FONCTIONS DE MISE À JOUR (toute la logique métier)
// =====================================================================

// Représentant légal
function updateLegalVisibility(root) {
    const val = getCheckedVal(root, 'legal_representation');
    const p1 = root.querySelector('#block_parent1');
    const p2 = root.querySelector('#block_parent2');
    const other = root.querySelector('#block_other');
    if (p1) p1.style.display = (val === 'both' || val === 'father_only') ? 'block' : 'none';
    if (p2) p2.style.display = (val === 'both' || val === 'mother_only') ? 'block' : 'none';
    if (other) other.style.display = (val === 'other') ? 'block' : 'none';
    updateCotisation(root);
}

function updateCotisation(root) {
    const val = getCheckedVal(root, 'legal_representation');
    let montant = 40;
    if (val === 'both') montant = 60;
    else if (val === 'other') montant = 0;
    setInner('membership_fee_amount', montant);
    updateRecapTotals();
}

function toggleSameAddress(root) {
    const cbSameAddr = root.querySelector('#same_address_as_parent1');
    const blockAddr2 = root.querySelector('#block_parent2_address');
    const blockCountry2 = root.querySelector('#block_parent2_country');
    if (cbSameAddr && blockAddr2 && blockCountry2) {
        const hide = cbSameAddr.checked;
        blockAddr2.style.display = hide ? 'none' : 'block';
        blockCountry2.style.display = hide ? 'none' : 'block';
    }
}

function toggleEmployerYes(root) {
    const block = root.querySelector('#block_employer_yes');
    if (block) {
        block.style.display = (getCheckedVal(root, 'employer_assistance') === 'yes') ? 'block' : 'none';
    }
}

function toggleEmployerBlock(root) {
    const chk = root.querySelector('#send_invoice_to_employer');
    const block = root.querySelector('#block_employer_id');
    if (chk && block) {
        block.style.display = chk.checked ? 'block' : 'none';
    }
}

// Forfaits
function updateForfaitMontant(selectEl, montantInput) {
    const selectedOption = selectEl.options[selectEl.selectedIndex];
    let montant = 0;
    if (selectedOption && selectedOption.value) {
        const text = selectedOption.text;
        const match = text.match(/(\d+(?:\.\d+)?)\s*CHF/);
        if (match) montant = parseFloat(match[1]);
    }
    montantInput.value = montant.toFixed(2);
    updateTotalMensuel();
    updateCotisation(document.getElementById('ecolage_form_root'));
    updateAllDiscounts();
}

function updateTotalMensuel() {
    let total = 0;
    document.querySelectorAll('.montant-mensuel').forEach(function(input) {
        const val = parseFloat(input.value);
        if (!isNaN(val)) total += val;
    });
    setInner('total_monthly_fee', total);
    updateAllDiscounts();
}

// Dépôt
function updateDepot(root) {
    const val = getCheckedVal(root, 'deposit_status');
    const montant = (val === 'unpaid') ? 1000 : 0;
    setInner('deposit_amount', montant);
    updateRecapTotals();
}

// Réductions
function getBaseMensuel() {
    let total = 0;
    document.querySelectorAll('.montant-mensuel').forEach(function(input) {
        const val = parseFloat(input.value);
        if (!isNaN(val)) total += val;
    });
    return total;
}

function getAfterSchoolTotal() {
    let total = 0;
    document.querySelectorAll('.after-school-montant').forEach(function(input) {
        const optionsDiv = input.closest('.after-school-options');
        if (optionsDiv && optionsDiv.style.display !== 'none') {
            const val = parseFloat(input.value);
            if (!isNaN(val)) total += val;
        }
    });
    return total;
}

function getNbStudents() {
    const root = document.getElementById('ecolage_form_root');
    if (!root) return 0;
    const existing = root.querySelectorAll('#students_list .student-line:not(.new-student)').length;
    const deleted = root.querySelectorAll('input[name^="delete_student_line_"]').length;
    const newAdded = root.querySelectorAll('#students_list .new-student').length;
    return Math.max(0, existing - deleted) + newAdded;
}

function updateIncomePercentage(feeAtMax) {
    const grossIncomeEl = document.getElementById('gross_annual_income');
    const grossIncome = grossIncomeEl ? (parseFloat(grossIncomeEl.value) || 0) : 0;
    const incomeEl = document.getElementById('income_percentage_display');
    if (!incomeEl) return;
    if (grossIncome > 0 && feeAtMax > 0) {
        incomeEl.value = ((feeAtMax * 12 / grossIncome) * 100).toFixed(2);
    } else {
        incomeEl.value = '0.00';
    }
}

function updateAllDiscounts() {
    const root = document.getElementById('ecolage_form_root');
    if (!root) return;
    const reductionRequested = getCheckedVal(root, 'reduction_requested') === '1';
    const blockReduction = root.querySelector('#block_reduction_yes');
    if (blockReduction) blockReduction.style.display = reductionRequested ? 'block' : 'none';

    if (!reductionRequested) {
        updateRecapTotals();
        return;
    }

    const nb = Math.min(getNbStudents(), 4);
    const maxChildrenDisc = CHILDREN_MAP[nb] || 0.0;

    const seniorityEl = document.getElementById('seniority_years');
    const seniorityVal = seniorityEl ? seniorityEl.value : '5';
    const maxSeniorityDisc = SENIORITY_MAP[seniorityVal] || 0.0;

    const applyChildrenCb = document.getElementById('apply_children_discount');
    const applySeniorityCb = document.getElementById('apply_seniority_discount');
    const applyChildren = applyChildrenCb ? applyChildrenCb.checked : false;
    const applySeniority = applySeniorityCb ? applySeniorityCb.checked : false;

    const childrenDisc = applyChildren ? maxChildrenDisc : 0.0;
    const seniorityDisc = applySeniority ? maxSeniorityDisc : 0.0;
    const maxTotalDisc = maxChildrenDisc + maxSeniorityDisc;

    const base = getBaseMensuel();

    const feeAfterChildren = base * (1 - childrenDisc / 100.0);
    const feeAfterSeniority = base * (1 - seniorityDisc / 100.0);
    const feeAtMax = base * (1 - maxTotalDisc / 100.0);

    setVal('max_children_discount_display', maxChildrenDisc);
    setVal('monthly_fee_after_children_display', feeAfterChildren);
    setVal('max_seniority_discount_display', maxSeniorityDisc);
    setVal('monthly_fee_after_seniority_display', feeAfterSeniority);
    setVal('max_total_discount_display', maxTotalDisc);
    setVal('monthly_fee_at_max_display', feeAtMax);

    const reductionMoindre = getCheckedVal(root, 'reduction_moindre') === '1';
    const blockMoindre = root.querySelector('#block_reduction_moindre');
    if (blockMoindre) blockMoindre.style.display = reductionMoindre ? 'block' : 'none';

    let requestedDisc = 0.0;
    if (reductionMoindre) {
        const rdInput = document.getElementById('requested_discount');
        if (rdInput) {
            requestedDisc = Math.min(parseFloat(rdInput.value) || 0, maxTotalDisc);
        }
    } else {
        requestedDisc = maxTotalDisc;
    }

    const feeAfterRequested = base * (1 - requestedDisc / 100.0);
    setVal('monthly_fee_after_requested_display', feeAfterRequested);

    updateIncomePercentage(feeAtMax);
    updateRecapTotals();
    updateSolidarityTotal();
}

// Solidarité
function getEcolageBeforeSolidarity() {
    const root = document.getElementById('ecolage_form_root');
    const reductionRequested = root ? getCheckedVal(root, 'reduction_requested') === '1' : false;
    if (!reductionRequested) return getBaseMensuel();
    const el = document.getElementById('monthly_fee_after_requested_display');
    return el ? (parseFloat(el.value) || 0) : getBaseMensuel();
}

function getEcolageAfterDiscount() {
    let base = getEcolageBeforeSolidarity();
    const root = document.getElementById('ecolage_form_root');
    const solidarityYes = root ? getCheckedVal(root, 'solidarity_request') === 'yes' : false;
    const applyIncrease = document.getElementById('apply_solidarity_increase');
    const percentInput = document.getElementById('solidarity_percentage');
    if (solidarityYes && applyIncrease && applyIncrease.checked && percentInput) {
        const percent = parseFloat(percentInput.value) || 0;
        if (percent > 0) base = base * (1 + percent / 100);
    }
    return base;
}

function updateSolidarityTotal() {
    const root = document.getElementById('ecolage_form_root');
    if (!root) return;
    const solidarityYes = getCheckedVal(root, 'solidarity_request') === 'yes';
    const blockSolidarity = root.querySelector('#block_solidarity_yes');
    if (blockSolidarity) blockSolidarity.style.display = solidarityYes ? 'block' : 'none';

    const applyIncrease = document.getElementById('apply_solidarity_increase');
    const percentInput = document.getElementById('solidarity_percentage');
    const totalField = document.getElementById('solidarity_total_amount');
    if (!totalField) return;

    const base = getEcolageBeforeSolidarity();
    const isChecked = applyIncrease && applyIncrease.checked;
    const percent = percentInput ? (parseFloat(percentInput.value) || 0) : 0;
    const total = (isChecked && percent > 0) ? base * (1 + percent / 100) : 0;
    totalField.value = total.toFixed(2);
}

// Récapitulatif
function updateRecapTotals() {
    const ecolageMonthly = getEcolageAfterDiscount();
    const afterMonthly = getAfterSchoolTotal();
    const totalMonthly = ecolageMonthly + afterMonthly;
    const annualTuition = ecolageMonthly * 12;
    const annualAfter = afterMonthly * 12;

    const membershipEl = document.getElementById('membership_fee_amount');
    const depositEl = document.getElementById('deposit_amount');
    const membership = membershipEl ? (parseFloat(membershipEl.innerText) || 0) : 0;
    const deposit = depositEl ? (parseFloat(depositEl.innerText) || 0) : 0;
    const totalAnnual = annualTuition + annualAfter + membership + deposit;

    setVal('recap_monthly_tuition', ecolageMonthly);
    setVal('recap_monthly_after_school', afterMonthly);
    setVal('recap_total_monthly', totalMonthly);
    setVal('recap_annual_tuition', annualTuition);
    setVal('recap_annual_after_school', annualAfter);
    setVal('recap_annual_membership', membership);
    setVal('recap_deposit', deposit);
    setVal('recap_total_annual', totalAnnual);

    const root = document.getElementById('ecolage_form_root');
    const paymentTerms = root ? getCheckedVal(root, 'payment_terms') : null;
    const additionalReduction = root ? getCheckedVal(root, 'additional_reduction_request') : null;
    const discountApplicable = (paymentTerms === 'annually' && additionalReduction !== '1');
    const discountBlock = document.getElementById('total_with_discount_block');
    const discountedInput = document.getElementById('recap_total_annual_discounted');

    if (discountApplicable) {
        if (discountBlock) discountBlock.style.display = 'block';
        if (discountedInput) discountedInput.value = (totalAnnual * 0.98).toFixed(2);
    } else {
        if (discountBlock) discountBlock.style.display = 'none';
    }
}

// Parascolaire
function updateAfterSchoolTotal() {
    let total = 0;
    document.querySelectorAll('.after-school-montant').forEach(function(input) {
        const optionsDiv = input.closest('.after-school-options');
        if (optionsDiv && optionsDiv.style.display !== 'none') {
            const val = parseFloat(input.value);
            if (!isNaN(val)) total += val;
        }
    });
    setInner('after_school_total_amount', total);
    updateRecapTotals();
}

function setMontant(studentLineId, montant) {
    const montantInput = document.querySelector('.after-school-montant[data-student-line-id="' + studentLineId + '"]');
    if (montantInput) montantInput.value = montant.toFixed(2);
}

function updateAfterSchoolMontant(studentLineId) {
    const optionsDiv = document.querySelector('.after-school-options[data-student-line-id="' + studentLineId + '"]');
    if (!optionsDiv) return;
    const selectedRadio = optionsDiv.querySelector('input[name^="accueil_type_"]:checked');
    if (!selectedRadio) { setMontant(studentLineId, 0); updateAfterSchoolTotal(); return; }
    const accueilValue = selectedRadio.value;
    const useJardinPrix = (accueilValue === 'jardin' || accueilValue === 'jardins_enfants');
    let total = 0;
    optionsDiv.querySelectorAll('.prestation-checkbox:checked').forEach(function(cb) {
        const prix = useJardinPrix ? cb.getAttribute('data-prix-jardin') : cb.getAttribute('data-prix-classe');
        const val = parseFloat(prix);
        if (!isNaN(val)) total += val;
    });
    setMontant(studentLineId, total);
    updateAfterSchoolTotal();
}

function filterPrestationsByAccueilType(optionsDiv) {
    const selectedRadio = optionsDiv.querySelector('input[name^="accueil_type_"]:checked');
    const prestationItems = optionsDiv.querySelectorAll('.prestation-item');
    if (!selectedRadio) {
        prestationItems.forEach(function(prestaDiv) {
            prestaDiv.style.display = 'none';
            const checkbox = prestaDiv.querySelector('input[type="checkbox"]');
            if (checkbox && checkbox.checked) checkbox.checked = false;
        });
        return;
    }
    const accueilValue = selectedRadio.value;
    prestationItems.forEach(function(prestaDiv) {
        const applicable = (prestaDiv.getAttribute('data-applicable') || 'both').toLowerCase().trim();
        const isBoth = (applicable === 'both' || applicable === '' || applicable === 'false');
        const visible = isBoth || (applicable === accueilValue);
        prestaDiv.style.display = visible ? '' : 'none';
        if (!visible) {
            const checkbox = prestaDiv.querySelector('input[type="checkbox"]');
            if (checkbox && checkbox.checked) checkbox.checked = false;
        }
    });
}

function initAfterSchoolForStudent(studentLineId) {
    const optionsDiv = document.querySelector('.after-school-options[data-student-line-id="' + studentLineId + '"]');
    if (!optionsDiv) return;
    optionsDiv.querySelectorAll('input[name^="accueil_type_' + studentLineId + '"]').forEach(function(radio) {
        radio.addEventListener('change', function() {
            filterPrestationsByAccueilType(optionsDiv);
            updateAfterSchoolMontant(studentLineId);
        });
    });
    optionsDiv.querySelectorAll('.prestation-checkbox').forEach(function(cb) {
        cb.addEventListener('change', function() { updateAfterSchoolMontant(studentLineId); });
    });
    filterPrestationsByAccueilType(optionsDiv);
    updateAfterSchoolMontant(studentLineId);
}

function initAfterSchoolOptions() {
    document.querySelectorAll('.after-school-toggle').forEach(function(cb) {
        function toggle() {
            const optionsDiv = cb.closest('.card-body').querySelector('.after-school-options');
            if (optionsDiv) {
                optionsDiv.style.display = cb.checked ? 'block' : 'none';
                updateAfterSchoolTotal();
            }
        }
        cb.removeEventListener('change', toggle);
        cb.addEventListener('change', toggle);
        toggle();
    });
    document.querySelectorAll('.after-school-options').forEach(function(optionsDiv) {
        let studentLineId = optionsDiv.getAttribute('data-student-line-id');
        if (!studentLineId) {
            const radio = optionsDiv.querySelector('input[name^="accueil_type_"]');
            if (radio) {
                const match = radio.name.match(/accueil_type_(\d+)/);
                if (match) studentLineId = match[1];
            }
        }
        if (studentLineId) {
            optionsDiv.setAttribute('data-student-line-id', studentLineId);
            initAfterSchoolForStudent(studentLineId);
        }
    });
    updateAfterSchoolTotal();
}

function toggleAfterSchool(root) {
    const block = root.querySelector('#block_after_school_yes');
    const isYes = (getCheckedVal(root, 'after_school_request') === 'yes');
    if (block) block.style.display = isYes ? 'block' : 'none';
    if (!isYes) {
        root.querySelectorAll('.after-school-toggle').forEach(function(toggle) {
            if (toggle.checked) {
                toggle.checked = false;
                toggle.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    }
    updateAfterSchoolTotal();
    updateRecapTotals();
}

// Budget en ligne
function attachBudgetEvents() {
    const onlineBlock = document.getElementById('block_budget_online');
    if (!onlineBlock) return;

    function updateBudgetTotals() {
        let revenusMadame = 0, revenusMonsieur = 0;
        let chargesMadame = 0, chargesMonsieur = 0;

        const revenusHeader = onlineBlock.querySelector('.text-success');
        if (revenusHeader) {
            const tbody = revenusHeader.closest('.mb-4').querySelector('table tbody');
            if (tbody) {
                tbody.querySelectorAll('tr').forEach(function(row) {
                    const categoryCell = row.querySelector('td:first-child');
                    if (categoryCell) {
                        const categoryName = categoryCell.innerText.trim();
                        const toIgnore = ['Salaire net (à titre indicatif)', 'Fortune (immobilière, etc)'];
                        if (toIgnore.includes(categoryName)) return;
                    }
                    const madame = row.querySelector('input[name^="montant_madame_"]');
                    const monsieur = row.querySelector('input[name^="montant_monsieur_"]');
                    if (madame && monsieur) {
                        revenusMadame += parseFloat(madame.value) || 0;
                        revenusMonsieur += parseFloat(monsieur.value) || 0;
                    }
                });
            }
        }

        const chargesHeader = onlineBlock.querySelector('.text-danger');
        if (chargesHeader) {
            const tbody2 = chargesHeader.closest('.mb-4').querySelector('table tbody');
            if (tbody2) {
                tbody2.querySelectorAll('tr').forEach(function(row) {
                    const madame = row.querySelector('input[name^="montant_madame_"]');
                    const monsieur = row.querySelector('input[name^="montant_monsieur_"]');
                    if (madame && monsieur) {
                        chargesMadame += parseFloat(madame.value) || 0;
                        chargesMonsieur += parseFloat(monsieur.value) || 0;
                    }
                });
            }
        }

        const totalRevenus = revenusMadame + revenusMonsieur;
        const totalCharges = chargesMadame + chargesMonsieur;
        const solde = totalRevenus - totalCharges;

        function setSpan(id, val) {
            const el = document.getElementById(id);
            if (el) el.innerText = val.toFixed(2);
        }
        setSpan('total_revenus_madame_span', revenusMadame);
        setSpan('total_revenus_monsieur_span', revenusMonsieur);
        setSpan('total_revenus_span', totalRevenus);
        setSpan('total_charges_madame_span', chargesMadame);
        setSpan('total_charges_monsieur_span', chargesMonsieur);
        setSpan('total_charges_span', totalCharges);
        setSpan('solde_span', solde);
    }

    onlineBlock.querySelectorAll('input[type="number"]').forEach(function(input) {
        input.removeEventListener('input', updateBudgetTotals);
        input.addEventListener('input', updateBudgetTotals);
    });
    updateBudgetTotals();
}

// Suppression élève (AJAX)
const csrfToken = getCsrfToken();

function deleteStudent(lineId, btnElement) {
    fetch('/my/ecolage/delete_student_line', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({ line_id: lineId })
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        const success = data.result ? data.result.success : (data.success || false);
        if (success) {
            const lineDiv = btnElement.closest('.student-line');
            if (lineDiv) lineDiv.remove();
            const forfaitDiv = document.querySelector('.forfait-line[data-line-id="' + lineId + '"]');
            if (forfaitDiv) forfaitDiv.remove();
            const afterCard = document.querySelector('.card.mb-3.border:has(.after-school-toggle[name="after_school_selected_' + lineId + '"])');
            if (afterCard) afterCard.remove();
            updateTotalMensuel();
            updateAllDiscounts();
            updateAfterSchoolTotal();
            updateRecapTotals();
            checkStudentInfoMsg();
        } else {
            const errorMsg = (data.result && data.result.error) || data.error || 'Impossible de supprimer';
            alert('Erreur : ' + errorMsg);
        }
    })
    .catch(function(error) {
        console.error('Erreur réseau:', error);
        alert('Erreur de connexion. Veuillez réessayer.');
    });
}

// Ajout élève (DOM)
function addNewStudent(root) {
    const template = document.querySelector('#new_student_template .card');
    if (!template) return;
    const clone = template.cloneNode(true);
    const removeBtn = clone.querySelector('.btn-remove-new-student');
    if (removeBtn) {
        removeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            clone.remove();
            checkStudentInfoMsg();
        });
    }
    root.querySelector('#students_list').appendChild(clone);
    checkStudentInfoMsg();
}

function checkStudentInfoMsg() {
    const root = document.getElementById('ecolage_form_root');
    if (!root) return;
    const infoDiv = root.querySelector('#new_student_info');
    if (!infoDiv) return;
    const hasNew = root.querySelector('#students_list .new-student') !== null;
    infoDiv.style.display = hasNew ? 'block' : 'none';
}

// Parrainage
function addSponsorship(root) {
    const template = document.querySelector('#new_sponsorship_template .card');
    if (!template) return;
    const clone = template.cloneNode(true);
    const removeBtn = clone.querySelector('.btn-remove-new-sponsorship');
    if (removeBtn) {
        removeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            clone.remove();
        });
    }
    root.querySelector('#sponsorship_list').appendChild(clone);
}

// Réduction complémentaire
function toggleAdditionalReductionVisibility(root) {
    const reductionMoindre = getCheckedVal(root, 'reduction_moindre') === '1';
    const blockQ = root.querySelector('#block_reduction_complementaire_question');
    const blockContent = root.querySelector('#block_additional_reduction');
    if (reductionMoindre) {
        if (blockQ) blockQ.style.display = 'none';
        if (blockContent) blockContent.style.display = 'none';
    } else {
        if (blockQ) blockQ.style.display = 'block';
        toggleAdditionalReduction(root);
    }
}

function toggleAdditionalReduction(root) {
    const checked = getCheckedVal(root, 'additional_reduction_request');
    const block = root.querySelector('#block_additional_reduction');
    if (block) block.style.display = (checked === '1') ? 'block' : 'none';
}

function toggleExplanatoryLetter(root) {
    const checked = getCheckedVal(root, 'explanatory_letter_mode');
    const blockUpload = root.querySelector('#block_letter_upload');
    const blockWrite = root.querySelector('#block_letter_write');
    if (!blockUpload || !blockWrite) return;
    const isWrite = (checked === 'write');
    blockUpload.style.display = isWrite ? 'none' : 'block';
    blockWrite.style.display = isWrite ? 'block' : 'none';
}

function toggleBudgetMethod(root) {
    const checked = getCheckedVal(root, 'budget_method');
    const blockUpload = root.querySelector('#block_budget_upload');
    const blockOnline = root.querySelector('#block_budget_online');
    if (!blockUpload || !blockOnline) return;
    const isOnline = (checked === 'online');
    blockUpload.style.display = isOnline ? 'none' : 'block';
    blockOnline.style.display = isOnline ? 'block' : 'none';
    if (isOnline) attachBudgetEvents();
}

function toggleMultiBilling(root) {
    const radioYes = root.querySelector('#multi_yes');
    const container = root.querySelector('#billing_amounts_container');
    const input1 = root.querySelector('#parent1_billing_amount');
    const input2 = root.querySelector('#parent2_billing_amount');
    if (radioYes && radioYes.checked) {
        if (container) container.style.display = 'flex';
        if (input1) input1.required = true;
        if (input2) input2.required = true;
    } else {
        if (container) container.style.display = 'none';
        if (input1) input1.required = false;
        if (input2) input2.required = false;
    }
}

// =====================================================================
// INITIALISATION GLOBALE
// =====================================================================
function initForm(root) {
    updateLegalVisibility(root);
    toggleSameAddress(root);
    toggleEmployerYes(root);
    toggleEmployerBlock(root);
    updateDepot(root);
    updateAllDiscounts();
    updateAfterSchoolTotal();
    updateRecapTotals();
    initAfterSchoolOptions();
    toggleAfterSchool(root);
    toggleAdditionalReductionVisibility(root);
    toggleExplanatoryLetter(root);
    toggleBudgetMethod(root);
    attachBudgetEvents();
    // Textareas data-initial
    root.querySelectorAll('textarea[data-initial]').forEach(function(textarea) {
        const v = textarea.getAttribute('data-initial') || '';
        if (textarea.value !== v) textarea.value = v;
    });
    checkStudentInfoMsg();
    // Forfaits existants
    root.querySelectorAll('.forfait-select').forEach(function(select) {
        const lineId = select.getAttribute('data-line-id');
        const montantInput = root.querySelector('.montant-mensuel[data-line-id="' + lineId + '"]');
        if (montantInput) updateForfaitMontant(select, montantInput);
    });
}

function attachDelegatedEvents(root) {
    console.log("attachDelegatedEvents appelée");
    console.log("Écouteurs installés pour legal_representation");
root.querySelectorAll('input[name="legal_representation"]').forEach(r => {
    console.log("radio trouvé :", r);
    r.addEventListener('change', () => {
        console.log("Événement change capturé sur radio");
    });
});
    root.addEventListener('change', function(e) {
        const target = e.target;
        if (target.name === 'legal_representation') {
            updateLegalVisibility(root);
            updateCotisation(root);
        }
        if (target.id === 'same_address_as_parent1') {
            toggleSameAddress(root);
        }
        if (target.name === 'employer_assistance') {
            toggleEmployerYes(root);
        }
        if (target.id === 'send_invoice_to_employer') {
            toggleEmployerBlock(root);
        }
        if (target.name === 'deposit_status') {
            updateDepot(root);
        }
        if (target.classList && target.classList.contains('forfait-select')) {
            const lineId = target.getAttribute('data-line-id');
            const montantInput = root.querySelector('.montant-mensuel[data-line-id="' + lineId + '"]');
            if (montantInput) updateForfaitMontant(target, montantInput);
        }
        if (target.name === 'reduction_requested' ||
            target.id === 'seniority_years' ||
            target.id === 'apply_children_discount' ||
            target.id === 'apply_seniority_discount' ||
            target.name === 'reduction_moindre') {
            updateAllDiscounts();
        }
        if (target.id === 'gross_annual_income') {
            updateAllDiscounts();
        }
        if (target.name === 'additional_reduction_request') {
            toggleAdditionalReduction(root);
            updateRecapTotals();
        }
        if (target.name === 'explanatory_letter_mode') {
            toggleExplanatoryLetter(root);
        }
        if (target.name === 'budget_method') {
            toggleBudgetMethod(root);
        }
        if (target.name === 'after_school_request') {
            toggleAfterSchool(root);
        }
        if (target.name === 'solidarity_request') {
            updateSolidarityTotal();
            updateRecapTotals();
        }
        if (target.id === 'apply_solidarity_increase' || target.id === 'solidarity_percentage') {
            updateSolidarityTotal();
            updateRecapTotals();
        }
        if (target.name === 'payment_terms' || target.name === 'additional_reduction_request') {
            updateRecapTotals();
        }
        if (target.id === 'multi_yes' || target.id === 'multi_no') {
            toggleMultiBilling(root);
        }
        if (target.classList && target.classList.contains('after-school-toggle')) {
            const optionsDiv = target.closest('.card-body').querySelector('.after-school-options');
            if (optionsDiv) {
                optionsDiv.style.display = target.checked ? 'block' : 'none';
                updateAfterSchoolTotal();
            }
        }
        if (target.name && target.name.startsWith('accueil_type_')) {
            const match = target.name.match(/accueil_type_(\d+)/);
            if (match) {
                const studentLineId = match[1];
                const optionsDiv = document.querySelector('.after-school-options[data-student-line-id="' + studentLineId + '"]');
                if (optionsDiv) {
                    filterPrestationsByAccueilType(optionsDiv);
                    updateAfterSchoolMontant(studentLineId);
                }
            }
        }
        if (target.classList && target.classList.contains('prestation-checkbox')) {
            const optionsDiv = target.closest('.after-school-options');
            if (optionsDiv) {
                const studentLineId = optionsDiv.getAttribute('data-student-line-id');
                if (studentLineId) updateAfterSchoolMontant(studentLineId);
            }
        }
    });

    root.addEventListener('input', function(e) {
        if (e.target.id === 'requested_discount') {
            const maxEl = document.getElementById('max_total_discount_display');
            const max = parseFloat(maxEl ? maxEl.value : 0) || 0;
            let val = parseFloat(e.target.value) || 0;
            if (val > max) {
                e.target.value = max;
                e.target.classList.add('is-invalid');
                let feedback = root.querySelector('#requested_discount_feedback');
                if (!feedback) {
                    feedback = document.createElement('div');
                    feedback.id = 'requested_discount_feedback';
                    feedback.className = 'invalid-feedback';
                    e.target.parentNode.appendChild(feedback);
                }
                feedback.innerText = 'La réduction ne peut pas dépasser ' + max.toFixed(1) + '%.';
                feedback.style.display = '';
            } else {
                e.target.classList.remove('is-invalid');
                const feedback = root.querySelector('#requested_discount_feedback');
                if (feedback) feedback.style.display = 'none';
            }
            updateAllDiscounts();
        }
    });

    root.addEventListener('click', function(e) {
        if (e.target.id === 'btn_add_student') {
            e.preventDefault();
            addNewStudent(root);
        }
        const removeStudentBtn = e.target.closest('.btn-remove-student');
        if (removeStudentBtn) {
            e.preventDefault();
            const lineId = removeStudentBtn.getAttribute('data-line-id');
            if (lineId) deleteStudent(lineId, removeStudentBtn);
        }
        const removeNewStudentBtn = e.target.closest('.btn-remove-new-student');
        if (removeNewStudentBtn) {
            e.preventDefault();
            const lineDiv = removeNewStudentBtn.closest('.student-line');
            if (lineDiv) lineDiv.remove();
            checkStudentInfoMsg();
        }
        if (e.target.id === 'btn_add_sponsorship') {
            e.preventDefault();
            addSponsorship(root);
        }
        const removeSponsorBtn = e.target.closest('.btn-remove-sponsorship');
        if (removeSponsorBtn) {
            e.preventDefault();
            const sponsorItem = removeSponsorBtn.closest('.sponsorship-item');
            if (sponsorItem) sponsorItem.remove();
        }
        const removeNewSponsorBtn = e.target.closest('.btn-remove-new-sponsorship');
        if (removeNewSponsorBtn) {
            e.preventDefault();
            const sponsorItem = removeNewSponsorBtn.closest('.sponsorship-item');
            if (sponsorItem) sponsorItem.remove();
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    console.log("DOMContentLoaded déclenché");
    function waitForForm() {
        const form = document.getElementById('ecolage_form_root');
        console.log("Recherche du formulaire, résultat :", form);
        if (form) {
            console.log("Formulaire trouvé, appel de initForm et attachDelegatedEvents");
            initForm(form);
            attachDelegatedEvents(form);
        } else {
            console.log("Formulaire non trouvé, nouvel essai dans 100ms");
            setTimeout(waitForForm, 100);
        }
    }
    waitForForm();
});

console.log("portal_dossier.js chargé - en attente du formulaire");