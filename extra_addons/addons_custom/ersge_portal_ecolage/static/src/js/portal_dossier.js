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
// GESTION DYNAMIQUE DES CHAMPS REQUIRED (conditionnels)
// =====================================================================
function updateConditionalRequired(root) {
    // Parent 2
    const parent2Block = document.getElementById('block_parent2');
    const parent2Inputs = root.querySelectorAll('#block_parent2 input[name^="parent2_"]');
    parent2Inputs.forEach(input => {
        if (parent2Block && parent2Block.style.display !== 'none') {
            input.setAttribute('required', 'required');
        } else {
            input.removeAttribute('required');
        }
    });

    // Autre représentant (sauf le champ "Précisez" déjà required)
    const otherBlock = document.getElementById('block_other');
    const otherInputs = root.querySelectorAll('#block_other input[name^="other_"]');
    otherInputs.forEach(input => {
        if (otherBlock && otherBlock.style.display !== 'none') {
            if (input.name !== 'legal_representation_other') {
                input.setAttribute('required', 'required');
            }
        } else {
            input.removeAttribute('required');
        }
    });

    // Employeur (si send_invoice_to_employer est coché)
    const employerBlock = document.getElementById('block_employer_id');
    const employerInputs = root.querySelectorAll('#block_employer_id input, #block_employer_id select');
    const sendToEmployer = root.querySelector('#send_invoice_to_employer')?.checked;
    employerInputs.forEach(input => {
        if (employerBlock && employerBlock.style.display !== 'none' && sendToEmployer) {
            input.setAttribute('required', 'required');
        } else {
            input.removeAttribute('required');
        }
    });
}

// =====================================================================
// FONCTION DE VALIDATION COMPLÈTE (obligatoire + format)
// =====================================================================
function validateRequiredAndFormat(root) {
    let errors = [];

    // Helper : vérifier email
    function isValidEmail(email) {
        const re = /^[^\s@]+@([^\s@]+\.)+[^\s@]+$/;
        return re.test(email);
    }

    // Helper : vérifier téléphone (chiffres, espaces, +, -)
    function isValidPhone(phone) {
        const re = /^[\d\s\+-]+$/;
        return re.test(phone);
    }

    // Helper : vérifier NPA (4 à 6 chiffres)
    function isValidZip(zip) {
        const re = /^\d{4,6}$/;
        return re.test(zip);
    }

    // ==================== 1. Représentation légale ====================
    const legalRep = root.querySelector('input[name="legal_representation"]:checked');
    if (!legalRep) errors.push("Représentation légale non choisie");

    // ==================== 2. Parent 1 ====================
    const p1_first = root.querySelector('input[name="parent1_firstname"]');
    const p1_last = root.querySelector('input[name="parent1_lastname"]');
    const p1_email = root.querySelector('input[name="parent1_email"]');
    const p1_street = root.querySelector('input[name="parent1_street"]');
    const p1_zip = root.querySelector('input[name="parent1_zip"]');
    const p1_city = root.querySelector('input[name="parent1_city"]');
    const p1_country = root.querySelector('select[name="parent1_country_id"]');
    const p1_phone = root.querySelector('input[name="parent1_phone"]');

    if (!p1_first || !p1_first.value.trim()) errors.push("Prénom Parent 1");
    if (!p1_last || !p1_last.value.trim()) errors.push("Nom Parent 1");
    if (!p1_email || !p1_email.value.trim()) errors.push("Email Parent 1");
    else if (!isValidEmail(p1_email.value.trim())) errors.push("Email Parent 1 invalide");
    if (!p1_street || !p1_street.value.trim()) errors.push("Rue Parent 1");
    if (!p1_zip || !p1_zip.value.trim()) errors.push("NPA Parent 1");
    else if (!isValidZip(p1_zip.value.trim())) errors.push("NPA Parent 1 (doit être composé de 4 à 6 chiffres)");
    if (!p1_city || !p1_city.value.trim()) errors.push("Ville Parent 1");
    if (!p1_country || !p1_country.value) errors.push("Pays Parent 1");
    if (p1_phone && p1_phone.value.trim() && !isValidPhone(p1_phone.value.trim())) errors.push("Téléphone mobile Parent 1 (caractères non autorisés)");

    // ==================== 3. Parent 2 (si bloc visible) ====================
    const parent2Block = document.getElementById('block_parent2');
    if (parent2Block && parent2Block.style.display !== 'none') {
        const p2_first = root.querySelector('input[name="parent2_firstname"]');
        const p2_last = root.querySelector('input[name="parent2_lastname"]');
        const p2_email = root.querySelector('input[name="parent2_email"]');
        const p2_street = root.querySelector('input[name="parent2_street"]');
        const p2_zip = root.querySelector('input[name="parent2_zip"]');
        const p2_city = root.querySelector('input[name="parent2_city"]');
        const p2_country = root.querySelector('select[name="parent2_country_id"]');
        const p2_phone = root.querySelector('input[name="parent2_phone"]');
        const sameAddr = root.querySelector('#same_address_as_parent1')?.checked;

        if (!p2_first || !p2_first.value.trim()) errors.push("Prénom Parent 2");
        if (!p2_last || !p2_last.value.trim()) errors.push("Nom Parent 2");
        if (!p2_email || !p2_email.value.trim()) errors.push("Email Parent 2");
        else if (!isValidEmail(p2_email.value.trim())) errors.push("Email Parent 2 invalide");
        if (!sameAddr) {
            if (!p2_street || !p2_street.value.trim()) errors.push("Rue Parent 2");
            if (!p2_zip || !p2_zip.value.trim()) errors.push("NPA Parent 2");
            else if (!isValidZip(p2_zip.value.trim())) errors.push("NPA Parent 2 (doit être composé de 4 à 6 chiffres)");
            if (!p2_city || !p2_city.value.trim()) errors.push("Ville Parent 2");
            if (!p2_country || !p2_country.value) errors.push("Pays Parent 2");
        }
        if (p2_phone && p2_phone.value.trim() && !isValidPhone(p2_phone.value.trim())) errors.push("Téléphone mobile Parent 2 (caractères non autorisés)");
    }

    // ==================== 4. Autre représentant (si bloc visible) ====================
    const otherBlock = document.getElementById('block_other');
    if (otherBlock && otherBlock.style.display !== 'none') {
        const other_precise = root.querySelector('input[name="legal_representation_other"]');
        const other_first = root.querySelector('input[name="other_firstname"]');
        const other_last = root.querySelector('input[name="other_lastname"]');
        const other_email = root.querySelector('input[name="other_email"]');
        const other_street = root.querySelector('input[name="other_street"]');
        const other_zip = root.querySelector('input[name="other_zip"]');
        const other_city = root.querySelector('input[name="other_city"]');
        const other_country = root.querySelector('select[name="other_country_id"]');
        const other_phone = root.querySelector('input[name="other_phone"]');

        if (!other_precise || !other_precise.value.trim()) errors.push("Précision autre représentant");
        if (!other_first || !other_first.value.trim()) errors.push("Prénom autre représentant");
        if (!other_last || !other_last.value.trim()) errors.push("Nom autre représentant");
        if (!other_email || !other_email.value.trim()) errors.push("Email autre représentant");
        else if (!isValidEmail(other_email.value.trim())) errors.push("Email autre représentant invalide");
        if (!other_street || !other_street.value.trim()) errors.push("Rue autre représentant");
        if (!other_zip || !other_zip.value.trim()) errors.push("NPA autre représentant");
        else if (!isValidZip(other_zip.value.trim())) errors.push("NPA autre représentant (doit être composé de 4 à 6 chiffres)");
        if (!other_city || !other_city.value.trim()) errors.push("Ville autre représentant");
        if (!other_country || !other_country.value) errors.push("Pays autre représentant");
        if (other_phone && other_phone.value.trim() && !isValidPhone(other_phone.value.trim())) errors.push("Téléphone autre représentant (caractères non autorisés)");
    }

    // ==================== 5. Élèves existants ====================
    const studentLines = root.querySelectorAll('.student-line:not(.new-student)');
    if (studentLines.length === 0) {
        errors.push("Au moins un élève");
    } else {
        studentLines.forEach((line, idx) => {
            const first = line.querySelector('input[name^="student_firstname_"]');
            const last = line.querySelector('input[name^="student_lastname_"]');
            const birth = line.querySelector('input[name^="student_birthdate_"]');
            if (!first || !first.value.trim()) errors.push(`Prénom élève ${idx+1}`);
            if (!last || !last.value.trim()) errors.push(`Nom élève ${idx+1}`);
            if (!birth || !birth.value) errors.push(`Date de naissance élève ${idx+1}`);
        });
    }

   // ==================== 6. Nouveaux élèves ====================
    const newStudents = root.querySelectorAll('.new-student');
    newStudents.forEach((line, idx) => {
        const first = line.querySelector('input[name^="new_student_firstname"]');
        const last = line.querySelector('input[name^="new_student_lastname"]');
        const birth = line.querySelector('input[name^="new_student_birthdate"]');
        
        const firstNameVal = first ? first.value.trim() : '';
        const lastNameVal = last ? last.value.trim() : '';
        const birthVal = birth ? birth.value : '';
        
        if (firstNameVal === '' && lastNameVal === '' && birthVal === '') {
            return;
        }
        
        if (!first || firstNameVal === '') errors.push(`Prénom nouvel élève ${idx+1}`);
        if (!last || lastNameVal === '') errors.push(`Nom nouvel élève ${idx+1}`);
        if (!birth || birthVal === '') errors.push(`Date de naissance nouvel élève ${idx+1}`);
    });

    // ==================== 7. Forfaits ====================
    const forfaitSelects = root.querySelectorAll('.forfait-select');
    forfaitSelects.forEach((select, idx) => {
        if (!select.value) {
            const studentLine = select.closest('.forfait-line');
            const studentName = studentLine ? (studentLine.querySelector('.card-header span')?.innerText || `élève ${idx+1}`) : `élève ${idx+1}`;
            errors.push(`Forfait pour ${studentName}`);
        }
    });

    // ==================== 8. Conditions générales ====================
    const terms = root.querySelector('input[name="terms_accepted"]');
    if (terms && !terms.checked) errors.push("Acceptation des conditions générales");

    // ==================== 9. Signature ====================
    const signature = root.querySelector('input[name="signature_text"]');
    if (signature && !signature.value.trim()) errors.push("Signature");

    // ==================== 10. Employeur ====================
    const sendToEmployer = root.querySelector('#send_invoice_to_employer');
    if (sendToEmployer && sendToEmployer.checked) {
        const employerName = root.querySelector('input[name="employer_name"]');
        const employerStreet = root.querySelector('input[name="employer_street"]');
        const employerZip = root.querySelector('input[name="employer_zip"]');
        const employerCity = root.querySelector('input[name="employer_city"]');
        const employerCountry = root.querySelector('select[name="employer_country_id"]');
        if (!employerName || !employerName.value.trim()) errors.push("Nom de l'employeur");
        if (!employerStreet || !employerStreet.value.trim()) errors.push("Adresse de l'employeur");
        if (!employerZip || !employerZip.value.trim()) errors.push("Code Postal de l'employeur");
        else if (!isValidZip(employerZip.value.trim())) errors.push("Code Postal employeur (doit être composé de 4 à 6 chiffres)");
        if (!employerCity || !employerCity.value.trim()) errors.push("Ville de l'employeur");
        if (!employerCountry || !employerCountry.value) errors.push("Pays de l'employeur");
    }

    // ==================== 11. Facturation divisée (si activée) ====================
    const multiBillingYes = root.querySelector('#multi_yes')?.checked;
    if (multiBillingYes) {
        const recipients = root.querySelectorAll('.billing-recipient');
        if (recipients.length === 0) {
            errors.push("Ajouter au moins un destinataire pour la facturation divisée");
        } else {
            recipients.forEach((recip, idx) => {
                const nameInput = recip.querySelector('input[name="billing_recipient_name[]"]');
                const amountInput = recip.querySelector('input[name="billing_recipient_amount[]"]');
                const streetInput = recip.querySelector('input[name="billing_recipient_street[]"]');
                const zipInput = recip.querySelector('input[name="billing_recipient_zip[]"]');
                const cityInput = recip.querySelector('input[name="billing_recipient_city[]"]');
                const countrySelect = recip.querySelector('select[name="billing_recipient_country_id[]"]');

                if (!nameInput || !nameInput.value.trim()) errors.push(`Nom du destinataire ${idx+1} manquant`);
                if (!amountInput || !amountInput.value.trim() || parseFloat(amountInput.value) <= 0) {
                    errors.push(`Montant du destinataire ${idx+1} invalide (doit être > 0)`);
                }
                // Optionnel : rendre l'adresse obligatoire
                // if (!streetInput || !streetInput.value.trim()) errors.push(`Adresse du destinataire ${idx+1} manquante`);
                // if (!zipInput || !zipInput.value.trim()) errors.push(`NPA du destinataire ${idx+1} manquant`);
                // if (!cityInput || !cityInput.value.trim()) errors.push(`Ville du destinataire ${idx+1} manquante`);
                // if (!countrySelect || !countrySelect.value) errors.push(`Pays du destinataire ${idx+1} manquant`);
            });
        }
    }

    return errors;
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
    updateConditionalRequired(root);
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
        updateConditionalRequired(root);
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
    setInner('base_monthly_fee_display', total);
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
    console.log('=== updateAllDiscounts ===');
    const reductionRequested = getCheckedVal(root, 'reduction_requested') === '1';
    console.log('reductionRequested :', reductionRequested);
    const blockReduction = root.querySelector('#block_reduction_yes');
    if (blockReduction) blockReduction.style.display = reductionRequested ? 'block' : 'none';

    // Base (total des forfaits)
    const base = getBaseMensuel();
    console.log('base :', base);

    // Si réduction non demandée, on réinitialise et on sort
    if (!reductionRequested) {
        setVal('monthly_fee_after_requested_display', base);
        updateRecapTotals();
        updateSolidarityTotal();
        updateFinalAmountBlock();
        console.log('réduction non demandée, monthly_fee_after_requested_display reset à base');
        return;
    }

    // Calcul des réductions max
    const nb = Math.min(getNbStudents(), 4);
    const maxChildrenDisc = CHILDREN_MAP[nb] || 0.0;
    console.log('maxChildrenDisc :', maxChildrenDisc);

    const seniorityEl = document.getElementById('seniority_years');
    const seniorityVal = seniorityEl ? seniorityEl.value : '5';
    const maxSeniorityDisc = SENIORITY_MAP[seniorityVal] || 0.0;
    console.log('maxSeniorityDisc :', maxSeniorityDisc);

    // État des cases à cocher
    const applyChildrenCb = document.getElementById('apply_children_discount');
    const applySeniorityCb = document.getElementById('apply_seniority_discount');
    const applyChildren = applyChildrenCb ? applyChildrenCb.checked : false;
    const applySeniority = applySeniorityCb ? applySeniorityCb.checked : false;
    console.log('applyChildren :', applyChildren);
    console.log('applySeniority :', applySeniority);

    // Réductions effectivement activées (0 si case décochée)
    const childrenDisc = applyChildren ? maxChildrenDisc : 0.0;
    const seniorityDisc = applySeniority ? maxSeniorityDisc : 0.0;
    const totalActiveDisc = childrenDisc + seniorityDisc;
    console.log('childrenDisc :', childrenDisc);
    console.log('seniorityDisc :', seniorityDisc);
    console.log('totalActiveDisc :', totalActiveDisc);

    // Affichage des rabais max (pour info)
    setVal('max_children_discount_display', maxChildrenDisc);
    setVal('monthly_fee_after_children_display', base * (1 - childrenDisc / 100.0));
    setVal('max_seniority_discount_display', maxSeniorityDisc);
    setVal('monthly_fee_after_seniority_display', base * (1 - seniorityDisc / 100.0));
    setVal('max_total_discount_display', maxChildrenDisc + maxSeniorityDisc);
    setVal('monthly_fee_at_max_display', base * (1 - (maxChildrenDisc + maxSeniorityDisc) / 100.0));

    // Gestion de la réduction moindre
    const reductionMoindre = getCheckedVal(root, 'reduction_moindre') === '1';
    const blockMoindre = root.querySelector('#block_reduction_moindre');
    if (blockMoindre) blockMoindre.style.display = reductionMoindre ? 'block' : 'none';

    let requestedDisc = 0.0;
    if (reductionMoindre) {
        const rdInput = document.getElementById('requested_discount');
        const val = rdInput ? parseFloat(rdInput.value) || 0 : 0;
        requestedDisc = Math.min(val, totalActiveDisc);
    } else {
        requestedDisc = totalActiveDisc;
    }
    console.log('requestedDisc :', requestedDisc);

    const feeAfterRequested = base * (1 - requestedDisc / 100.0);
    console.log('feeAfterRequested :', feeAfterRequested);
    setVal('monthly_fee_after_requested_display', feeAfterRequested);

    // Mise à jour du pourcentage de revenu (si applicable)
    updateIncomePercentage(base * (1 - (maxChildrenDisc + maxSeniorityDisc) / 100.0));

    // Rafraîchir les totaux
    updateRecapTotals();
    updateSolidarityTotal();
    updateFinalAmountBlock();
    console.log('fin updateAllDiscounts');
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
    const percentInput = document.getElementById('solidarity_percentage');
    if (solidarityYes && percentInput) {
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

    const percentInput = document.getElementById('solidarity_percentage');
    const totalField = document.getElementById('solidarity_total_amount');
    if (!totalField) return;

    // Récupérer la base : d'abord le montant après réduction, sinon le total mensuel hors réduction
    let base = 0;
    const afterReductionField = document.getElementById('monthly_fee_after_requested_display');
    if (afterReductionField && afterReductionField.value) {
        base = parseFloat(afterReductionField.value) || 0;
    }
    if (base === 0) {
        const totalMonthlyField = document.getElementById('total_monthly_fee');
        if (totalMonthlyField && totalMonthlyField.innerText) {
            base = parseFloat(totalMonthlyField.innerText) || 0;
        }
    }

    const percent = percentInput ? (parseFloat(percentInput.value) || 0) : 0;
    const total = (solidarityYes && percent > 0) ? base * (1 + percent / 100) : base;
    totalField.value = total.toFixed(2);
}

// ---------- Fonctions pour l'option CEF / proposition simple ----------
function toggleCefOrProposal() {
    const isCef = document.getElementById('cef_agreement')?.checked;
    const blockSimple = document.getElementById('block_proposal_simple');
    const blockCef = document.getElementById('block_cef_agreement');
    if (blockSimple) blockSimple.style.display = isCef ? 'none' : 'block';
    if (blockCef) blockCef.style.display = isCef ? 'block' : 'none';
    
        // Vider le champ opposé
    if (isCef) {
        document.getElementById('proposed_monthly_amount').value = '';
    } else {
        document.getElementById('proposed_monthly_fee_cef').value = '';
    }
    // Masquer le warning de la proposition simple lorsqu'on bascule sur CEF
    const warningBlock = document.getElementById('proposal_warning_block');
    if (warningBlock) warningBlock.style.display = 'none';
    // Recalculer le pourcentage de la proposition (si un champ est rempli)
    updateProposalPercentage();
}

function updateCefIncrease() {
    const previous = parseFloat(document.getElementById('previous_monthly_fee')?.value || 0);
    const proposed = parseFloat(document.getElementById('proposed_monthly_fee_cef')?.value || 0);
    const infoSpan = document.getElementById('cef_increase_info');
    if (infoSpan && previous > 0 && proposed > 0) {
        const increase = ((proposed / previous) - 1) * 100;
        if (increase >= 6) {
            infoSpan.innerHTML = `<span class="text-success">✓ Augmentation de ${increase.toFixed(2)}% (≥6% requis).</span>`;
        } else {
            infoSpan.innerHTML = `<span class="text-danger">✗ L'augmentation doit être d'au moins 6% (actuellement ${increase.toFixed(2)}%).</span>`;
        }
    } else if (infoSpan) {
        infoSpan.innerHTML = '';
    }
}

// ---------- Fonction pour le calcul du pourcentage de la proposition ----------
function updateProposalPercentage() {
    // Déterminer quel champ de montant est actif (CEF ou simple)
    const isCef = document.getElementById('cef_agreement')?.checked;
    let monthly = 0;
    if (isCef) {
        monthly = parseFloat(document.getElementById('proposed_monthly_fee_cef')?.value || 0);
    } else {
        monthly = parseFloat(document.getElementById('proposed_monthly_amount')?.value || 0);
    }
    const annualIncome = parseFloat(document.getElementById('proposal_annual_income')?.value || 0);
    const percentageDisplay = document.getElementById('proposal_percentage_display');
    const warningBlock = document.getElementById('proposal_warning_block');

    if (percentageDisplay) {
        if (annualIncome > 0 && monthly > 0) {
            const annualProposal = monthly * 12;
            const percentage = (annualProposal / annualIncome) * 100;
            percentageDisplay.value = percentage.toFixed(2);
            if (warningBlock) {
                warningBlock.style.display = percentage < 14 ? 'block' : 'none';
            }
        } else {
            percentageDisplay.value = '0.00';
            if (warningBlock) warningBlock.style.display = 'none';
        }
    }
}

// =====================================================================
// TOGGLE PARRAINAGE
// =====================================================================
function toggleSponsorship(root) {
    const block = root.querySelector('#block_sponsorship_yes');
    if (!block) return;
    const val = getCheckedVal(root, 'sponsorship_request');
    block.style.display = (val === 'yes') ? 'block' : 'none';
    // Gestion des champs requis (optionnel mais recommandé)
    const inputs = block.querySelectorAll('input, select');
    inputs.forEach(input => {
        if (val === 'yes') {
            input.setAttribute('required', 'required');
        } else {
            input.removeAttribute('required');
        }
    });
}

// =====================================================================
// GESTION DYNAMIQUE DES DESTINATAIRES DE FACTURATION (AVEC ADRESSE)
// =====================================================================

function addBillingRecipient(root) {
    const template = root.querySelector('#new_billing_recipient_template .billing-recipient');
    if (!template) return;
    const clone = template.cloneNode(true);
    // Réinitialiser les valeurs
    clone.querySelector('input[name="billing_recipient_name[]"]').value = '';
    clone.querySelector('input[name="billing_recipient_amount[]"]').value = '0.00';
    clone.querySelector('input[name="billing_recipient_street[]"]').value = '';
    clone.querySelector('input[name="billing_recipient_zip[]"]').value = '';
    clone.querySelector('input[name="billing_recipient_city[]"]').value = '';
    const select = clone.querySelector('select[name="billing_recipient_country_id[]"]');
    if (select) select.selectedIndex = 0;
    // Gérer la suppression
    const removeBtn = clone.querySelector('.btn-remove-billing');
    if (removeBtn) {
        removeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            clone.remove();
            toggleMultiBilling(root);
        });
    }
    const list = root.querySelector('#billing_recipients_list');
    if (list) list.appendChild(clone);
    toggleMultiBilling(root);
}

function toggleMultiBilling(root) {
    const radioYes = root.querySelector('#multi_yes');
    const container = root.querySelector('#billing_amounts_container');
    if (!container) return;
    if (radioYes && radioYes.checked) {
        container.style.display = 'flex';
        // S'assurer qu'il y a au moins un destinataire
        const list = container.querySelector('#billing_recipients_list');
        if (list && list.querySelectorAll('.billing-recipient').length === 0) {
            addBillingRecipient(root);
        }
        // Rendre les champs obligatoires (nom et montant uniquement)
        container.querySelectorAll('input[name="billing_recipient_name[]"], input[name="billing_recipient_amount[]"]').forEach(function(input) {
            input.setAttribute('required', 'required');
        });
        // Les champs adresse restent optionnels
    } else {
        container.style.display = 'none';
        // Enlever les required
        container.querySelectorAll('input[name="billing_recipient_name[]"], input[name="billing_recipient_amount[]"]').forEach(function(input) {
            input.removeAttribute('required');
        });
    }
}

// =====================================================================
// MISE À JOUR DU BLOC MONTANT FINAL (récapitulatif)
// =====================================================================
function updateFinalAmountBlock() {
    const root = document.getElementById('ecolage_form_root');
    if (!root) return;

    // 1. Base (somme des forfaits)
    const base = getBaseMensuel();

    // 2. Montant après réduction standard
    const reductionRequested = getCheckedVal(root, 'reduction_requested') === '1';
    let standardMonthly = base;
    if (reductionRequested) {
        const afterReductionField = document.getElementById('monthly_fee_after_requested_display');
        const val = afterReductionField ? parseFloat(afterReductionField.value) : NaN;
        if (!isNaN(val) && val >= 0) {
            standardMonthly = val;
        }
    }
    setVal('final_amount_after_standard_reduction', standardMonthly);

    // 3. Cas particuliers (solidarité / propositions)
    const solidarityYes = getCheckedVal(root, 'solidarity_request') === 'yes';
    const additionalReduction = getCheckedVal(root, 'additional_reduction_request') === '1';

    const solidarityBlock = document.getElementById('final_amount_solidarity_block');
    const simpleBlock = document.getElementById('final_amount_proposal_simple_block');
    const cefBlock = document.getElementById('final_amount_proposal_cef_block');
    const noBlock = document.getElementById('final_amount_no_particular_block');

    if (solidarityBlock) solidarityBlock.style.display = 'none';
    if (simpleBlock) simpleBlock.style.display = 'none';
    if (cefBlock) cefBlock.style.display = 'none';
    if (noBlock) noBlock.style.display = 'block';

    if (solidarityYes) {
        const solidarityTotalField = document.getElementById('solidarity_total_amount');
        const solidarityValue = solidarityTotalField ? parseFloat(solidarityTotalField.value) || 0 : 0;
        const valueSpan = document.getElementById('final_amount_solidarity_value');
        if (valueSpan) valueSpan.innerText = solidarityValue.toFixed(2);
        if (solidarityBlock) solidarityBlock.style.display = 'block';
        if (noBlock) noBlock.style.display = 'none';
    } else if (additionalReduction) {
        const proposalType = root.querySelector('input[name="cef_or_proposal"]:checked')?.value;
        if (proposalType === 'simple') {
            const proposedAmount = document.getElementById('proposed_monthly_amount');
            const val = proposedAmount ? parseFloat(proposedAmount.value) || 0 : 0;
            const valueSpan = document.getElementById('final_amount_proposal_simple_value');
            if (valueSpan) valueSpan.innerText = val.toFixed(2);
            if (simpleBlock) simpleBlock.style.display = 'block';
            if (noBlock) noBlock.style.display = 'none';
        } else if (proposalType === 'cef') {
            const proposedCef = document.getElementById('proposed_monthly_fee_cef');
            const val = proposedCef ? parseFloat(proposedCef.value) || 0 : 0;
            const valueSpan = document.getElementById('final_amount_proposal_cef_value');
            if (valueSpan) valueSpan.innerText = val.toFixed(2);
            if (cefBlock) cefBlock.style.display = 'block';
            if (noBlock) noBlock.style.display = 'none';
        }
    }
    updateProposedTotal();
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

    // Mise à jour du total hors réduction (base)
    setInner('base_monthly_fee_display', getBaseMensuel());

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

    updateFinalAmountBlock();
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

// --- Toggle Réduction complémentaire selon Solidarité (ajout) ---
function toggleComplementaryReduction() {
    const solidarityYes = document.querySelector('input[name="solidarity_request"]:checked')?.value === 'yes';
    const reductionComplementBlock = document.getElementById('block_reduction_complementaire_question');
    if (reductionComplementBlock) {
        reductionComplementBlock.style.display = solidarityYes ? 'none' : 'block';
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
    // Écouteurs explicites pour les cases à cocher de réduction
    const applyChildren = document.getElementById('apply_children_discount');
    const applySeniority = document.getElementById('apply_seniority_discount');

    if (applyChildren) {
        applyChildren.addEventListener('change', function() {
            console.log('Case enfants changée, checked =', this.checked);
            updateAllDiscounts();
        });
    }
    if (applySeniority) {
        applySeniority.addEventListener('change', function() {
            console.log('Case ancienneté changée, checked =', this.checked);
            updateAllDiscounts();
        });
    }

    // Toggle familles liées (initialisation + écouteur direct)
    const toggleLinked = document.getElementById('toggle_linked_families');
    const blockLinked  = document.getElementById('block_linked_families');
    if (toggleLinked && blockLinked) {
        blockLinked.style.display = toggleLinked.checked ? 'block' : 'none';
        toggleLinked.addEventListener('change', function() {
            blockLinked.style.display = this.checked ? 'block' : 'none';
            if (!this.checked) {
                const textarea = document.querySelector('textarea[name="linked_families_comment_text"]');
                if (textarea) textarea.value = '';
            }
        });
    }

    // Forfaits existants
    root.querySelectorAll('.forfait-select').forEach(function(select) {
        const lineId = select.getAttribute('data-line-id');
        const montantInput = root.querySelector('.montant-mensuel[data-line-id="' + lineId + '"]');
        if (montantInput) updateForfaitMontant(select, montantInput);
    });

    // Mise à jour initiale des required conditionnels
    updateConditionalRequired(root);
    // Initialisation de l'affichage de la réduction complémentaire selon solidarité
    toggleComplementaryReduction();
    // Initialisation des blocs CEF / proposition simple
    toggleCefOrProposal();
    updateCefIncrease();
    // Initialisation du calcul du pourcentage de la proposition
    updateProposalPercentage();
    // Mise à jour du bloc final
    updateFinalAmountBlock();

    // AJOUT : toggle parrainage
    toggleSponsorship(root);

    // AJOUT : toggle facturation divisée (avec adresse)
    toggleMultiBilling(root);

    // FORCER LA MISE À JOUR DES TOTAUX APRÈS CHARGEMENT DES FORFAITS
    setTimeout(function() {
        updateTotalMensuel();     // Met à jour base_monthly_fee_display
        updateRecapTotals();      // Met à jour tous les récapitulatifs
    }, 300);

    // Forcer la mise à jour de la solidarité après un court délai
    setTimeout(function() {
        updateSolidarityTotal();
    }, 100);
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
            toggleComplementaryReduction();
        }
        if (target.id === 'solidarity_percentage') {
            updateSolidarityTotal();
            updateRecapTotals();
        }
        // Gestion CEF
        if (target.name === 'cef_or_proposal') {
            toggleCefOrProposal();
            updateFinalAmountBlock();
        }
        if (target.id === 'previous_monthly_fee' || target.id === 'proposed_monthly_fee_cef') {
            updateCefIncrease();
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
        // AJOUT : Toggle parrainage
        if (target.name === 'sponsorship_request') {
            toggleSponsorship(root);
        }
        // Le bloc toggle_linked_families est déjà traité dans initForm
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
        if (e.target.id === 'solidarity_percentage') {
            updateSolidarityTotal();
            updateRecapTotals();
        }
        if (e.target.id === 'monthly_fee_after_requested_display') {
            updateSolidarityTotal();
        }
        if (e.target.id === 'previous_monthly_fee' || e.target.id === 'proposed_monthly_fee_cef') {
            updateCefIncrease();
        }
        // Mise à jour du pourcentage de la proposition
        if (e.target.id === 'proposed_monthly_amount' || e.target.id === 'proposal_annual_income' || e.target.id === 'proposed_monthly_fee_cef') {
            updateProposalPercentage();
            updateFinalAmountBlock();
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
        // AJOUT : Gestion des destinataires de facturation
        if (e.target.id === 'btn_add_billing') {
            e.preventDefault();
            addBillingRecipient(root);
        }
        const removeBillingBtn = e.target.closest('.btn-remove-billing');
        if (removeBillingBtn) {
            e.preventDefault();
            const recipientItem = removeBillingBtn.closest('.billing-recipient');
            if (recipientItem) {
                recipientItem.remove();
                // Mettre à jour les required
                toggleMultiBilling(root);
            }
        }
    });
}

// =====================================================================
// GÉNÉRATION DU RÉCAPITULATIF (CORRECTION DROIT À L'IMAGE)
// =====================================================================
function generateRecap(form) {
    let html = '<div class="row">';

    // ---------- 1. Représentation légale ----------
    const legalRep = form.querySelector('input[name="legal_representation"]:checked');
    const legalRepValue = legalRep ? legalRep.value : '';
    let legalRepText = '';
    switch (legalRepValue) {
        case 'both': legalRepText = 'Les deux parents'; break;
        case 'father_only': legalRepText = 'Parent 1 uniquement'; break;
        case 'mother_only': legalRepText = 'Parent 2 uniquement'; break;
        case 'other': legalRepText = 'Autre'; break;
        default: legalRepText = 'Non renseigné';
    }
    html += `<div class="col-12 mb-3"><strong>Représentation légale :</strong> ${legalRepText}</div>`;

    // Parent 1
    const p1_first = form.querySelector('input[name="parent1_firstname"]')?.value || '';
    const p1_last = form.querySelector('input[name="parent1_lastname"]')?.value || '';
    const p1_email = form.querySelector('input[name="parent1_email"]')?.value || '';
    const p1_phone = form.querySelector('input[name="parent1_phone"]')?.value || '';
    html += `<div class="col-md-6"><strong>Parent 1 :</strong> ${p1_first} ${p1_last}<br>📧 ${p1_email}<br>📞 ${p1_phone}</div>`;

    // Parent 2
    const p2_first = form.querySelector('input[name="parent2_firstname"]')?.value || '';
    const p2_last = form.querySelector('input[name="parent2_lastname"]')?.value || '';
    const p2_email = form.querySelector('input[name="parent2_email"]')?.value || '';
    const p2_phone = form.querySelector('input[name="parent2_phone"]')?.value || '';
    html += `<div class="col-md-6"><strong>Parent 2 :</strong> ${p2_first} ${p2_last}<br>📧 ${p2_email}<br>📞 ${p2_phone}</div>`;

    // Autre représentant
    if (legalRepValue === 'other') {
        const other_first = form.querySelector('input[name="other_firstname"]')?.value || '';
        const other_last = form.querySelector('input[name="other_lastname"]')?.value || '';
        const other_email = form.querySelector('input[name="other_email"]')?.value || '';
        html += `<div class="col-12 mt-2"><strong>Autre représentant :</strong> ${other_first} ${other_last} (${other_email})</div>`;
    }

    // Adresse commune ou séparée ? (optionnel)
    const sameAddr = form.querySelector('#same_address_as_parent1')?.checked;
    html += `<div class="col-12"><small>Adresse parent 2 ${sameAddr ? 'identique au parent 1' : 'différente'}</small></div>`;

    // ---------- 2. Élèves ----------
    const students = form.querySelectorAll('.student-line:not(.new-student)');
    if (students.length) {
        html += `<div class="col-12 mt-3"><h6>📚 Élèves inscrits</h6><ul>`;
        students.forEach(stud => {
            const first = stud.querySelector('input[name^="student_firstname_"]')?.value || '';
            const last = stud.querySelector('input[name^="student_lastname_"]')?.value || '';
            const birth = stud.querySelector('input[name^="student_birthdate_"]')?.value || '';
            const gender = stud.querySelector('select[name^="student_gender_"]')?.value === 'M' ? 'Masculin' : (stud.querySelector('select[name^="student_gender_"]')?.value === 'F' ? 'Féminin' : '');
            // Récupération du droit à l'image (radio)
            let imageRightValue = '';
            const radioChecked = stud.querySelector('input[type="radio"][name^="student_image_rights_"]:checked');
            if (radioChecked) {
                const val = radioChecked.value;
                if (val === 'no') imageRightValue = '❌ Refus';
                else if (val === 'internal') imageRightValue = '✅ Accord (interne)';
                else if (val === 'internal_external') imageRightValue = '✅ Accord (interne et externe)';
            }
            const imageRights = imageRightValue || 'Non spécifié';
            html += `<li><strong>${first} ${last}</strong> (né(e) le ${birth}, ${gender}) - Droit à l'image : ${imageRights}</li>`;
        });
        html += `</ul></div>`;
    }

    // ---------- 3. Forfaits (écolage) ----------
    let totalMensuelBase = 0;
    const forfaitLines = document.querySelectorAll('.forfait-line');
    if (forfaitLines.length) {
        html += `<div class="col-12 mt-3"><h6>🎓 Forfaits sélectionnés</h6><ul>`;
        forfaitLines.forEach(line => {
            const studentName = line.querySelector('.card-header span')?.innerText || 'Élève';
            const forfaitSelect = line.querySelector('.forfait-select');
            const selectedOption = forfaitSelect?.options[forfaitSelect.selectedIndex];
            const forfaitName = selectedOption?.text.split(' -')[0] || 'Aucun';
            const montantInput = line.querySelector('.montant-mensuel');
            const montant = parseFloat(montantInput?.value) || 0;
            totalMensuelBase += montant;
            html += `<li><strong>${studentName}</strong> : ${forfaitName} → ${montant.toFixed(2)} CHF/mois</li>`;
        });
        html += `</ul></div>`;
    }
    html += `<div class="col-12"><strong>💰 Total mensuel écolage (hors réductions) :</strong> ${totalMensuelBase.toFixed(2)} CHF</div>`;

    // ---------- 4. Réductions demandées ----------
    const reductionRequested = form.querySelector('input[name="reduction_requested"]:checked')?.value;
    if (reductionRequested === '1') {
        html += `<div class="col-12 mt-3"><h6>🔻 Réductions sollicitées</h6>`;
        const applyChildren = document.getElementById('apply_children_discount')?.checked;
        const maxChildren = document.getElementById('max_children_discount_display')?.value || '0';
        html += `<div>👨‍👩‍👧‍👦 Rabais nombre d'enfants : ${applyChildren ? '✅ Demandé' : '❌ Non demandé'} (max ${maxChildren}%)</div>`;
        const seniorityYears = document.getElementById('seniority_years')?.options[document.getElementById('seniority_years')?.selectedIndex]?.text || '';
        const applySeniority = document.getElementById('apply_seniority_discount')?.checked;
        const maxSeniority = document.getElementById('max_seniority_discount_display')?.value || '0';
        html += `<div>📅 Ancienneté : ${seniorityYears} - Rabais : ${applySeniority ? '✅ Demandé' : '❌ Non demandé'} (max ${maxSeniority}%)</div>`;
        const reductionMoindre = form.querySelector('input[name="reduction_moindre"]:checked')?.value === '1';
        let requestedDiscount = '0';
        if (reductionMoindre) {
            requestedDiscount = document.getElementById('requested_discount')?.value || '0';
            html += `<div>✏️ Réduction moindre demandée : ${requestedDiscount}%</div>`;
        } else {
            const maxTotal = document.getElementById('max_total_discount_display')?.value || '0';
            html += `<div>🔝 Réduction maximale sollicitée : ${maxTotal}%</div>`;
        }
        const finalMonthly = document.getElementById('monthly_fee_after_requested_display')?.value || totalMensuelBase;
        html += `<div><strong>💵 Total mensuel après réduction :</strong> ${parseFloat(finalMonthly).toFixed(2)} CHF</div>`;
        html += `</div>`;
    }

    // ---------- 5. Réduction complémentaire ----------
    const additionalReduction = form.querySelector('input[name="additional_reduction_request"]:checked')?.value === '1';
    if (additionalReduction) {
        html += `<div class="col-12 mt-3"><h6>📄 Demande de réduction complémentaire</h6>`;
        const grossIncome = document.getElementById('gross_annual_income')?.value || '0';
        const incomePercent = document.getElementById('income_percentage_display')?.value || '0';
        const proposedAmount = form.querySelector('input[name="proposed_monthly_amount"]')?.value || '0';
        html += `<div>💰 Revenu brut annuel : ${parseFloat(grossIncome).toFixed(2)} CHF</div>`;
        html += `<div>📊 Pourcentage du tarif sur revenu : ${incomePercent}%</div>`;
        html += `<div>✉️ Écolage mensuel proposé : ${parseFloat(proposedAmount).toFixed(2)} CHF</div>`;
        const explanatoryMode = form.querySelector('input[name="explanatory_letter_mode"]:checked')?.value;
        html += `<div>📎 Justificatifs : avis de taxation + fiches de salaire + lettre explicative (${explanatoryMode === 'write' ? 'écrite' : 'fichier joint'})</div>`;
        html += `</div>`;
    }

    // ---------- 6. Parascolaire ----------
    const afterSchoolRequest = form.querySelector('input[name="after_school_request"]:checked')?.value;
    if (afterSchoolRequest === 'yes') {
        html += `<div class="col-12 mt-3"><h6>🏫 Parascolaire</h6>`;
        const afterTotal = document.getElementById('after_school_total_amount')?.innerText || '0.00';
        html += `<div>Demande d’inscription : Oui</div>`;
        const afterToggles = form.querySelectorAll('.after-school-toggle:checked');
        if (afterToggles.length) {
            html += `<ul>`;
            afterToggles.forEach(toggle => {
                const studentCard = toggle.closest('.card');
                const studentName = studentCard?.querySelector('.card-header')?.innerText || 'Élève';
                const accueilType = studentCard?.querySelector('input[name^="accueil_type_"]:checked')?.parentElement?.innerText || '';
                const montant = studentCard?.querySelector('.after-school-montant')?.value || '0';
                html += `<li>${studentName} : ${accueilType} → ${parseFloat(montant).toFixed(2)} CHF/mois</li>`;
            });
            html += `</ul>`;
        }
        html += `<div><strong>💰 Total mensuel parascolaire :</strong> ${parseFloat(afterTotal).toFixed(2)} CHF</div>`;
        html += `</div>`;
    } else {
        html += `<div class="col-12 mt-3"><strong>🏫 Parascolaire :</strong> Non demandé</div>`;
    }

    // ---------- 7. Solidarité ----------
    const solidarityRequest = form.querySelector('input[name="solidarity_request"]:checked')?.value;
    if (solidarityRequest === 'yes') {
        const applySolidarity = document.getElementById('apply_solidarity_increase')?.checked;
        const solidarityPercent = document.getElementById('solidarity_percentage')?.value || '0';
        const solidarityTotal = document.getElementById('solidarity_total_amount')?.value || '0';
        html += `<div class="col-12 mt-3"><h6>🤝 Solidarité</h6>`;
        html += `<div>Contribution au fonds : ${applySolidarity ? `Oui (+${solidarityPercent}%)` : 'Non'}</div>`;
        if (applySolidarity) html += `<div>Montant mensuel total après solidarité : ${parseFloat(solidarityTotal).toFixed(2)} CHF</div>`;
        html += `</div>`;
    }

    // ---------- 8. Parrainage ----------
    const sponsorshipRequest = form.querySelector('input[name="sponsorship_request"]:checked')?.value;
    if (sponsorshipRequest === 'yes') {
        const sponsors = form.querySelectorAll('.sponsorship-item');
        if (sponsors.length) {
            html += `<div class="col-12 mt-3"><h6>🤝 Parrainage</h6><ul>`;
            sponsors.forEach(sp => {
                const first = sp.querySelector('input[name^="sp_firstname_"]')?.value || '';
                const last = sp.querySelector('input[name^="sp_lastname_"]')?.value || '';
                const amount = sp.querySelector('input[name^="sp_amount_"]')?.value || '0';
                html += `<li>${first} ${last} : ${parseFloat(amount).toFixed(2)} CHF/mois</li>`;
            });
            html += `</ul></div>`;
        }
    }

    // ---------- 9. Facturation (mode de paiement, division) ----------
    const paymentTerms = form.querySelector('input[name="payment_terms"]:checked')?.value;
    let paymentText = paymentTerms === 'monthly' ? 'Mensuel (avant le 10)' : 'Annuel (avant le 30 septembre, déduction 2%)';
    html += `<div class="col-12 mt-3"><strong>💳 Mode de paiement :</strong> ${paymentText}</div>`;
    const multiBilling = form.querySelector('input[name="multi_billing_request"]:checked')?.value === '1';
    if (multiBilling) {
        const recipients = form.querySelectorAll('.billing-recipient');
        html += `<div><strong>📑 Facturation divisée :</strong><ul>`;
        recipients.forEach(recip => {
            const name = recip.querySelector('input[name="billing_recipient_name[]"]')?.value || '';
            const amount = recip.querySelector('input[name="billing_recipient_amount[]"]')?.value || '0';
            const street = recip.querySelector('input[name="billing_recipient_street[]"]')?.value || '';
            const zip = recip.querySelector('input[name="billing_recipient_zip[]"]')?.value || '';
            const city = recip.querySelector('input[name="billing_recipient_city[]"]')?.value || '';
            const countrySelect = recip.querySelector('select[name="billing_recipient_country_id[]"]');
            const countryName = countrySelect ? countrySelect.options[countrySelect.selectedIndex]?.text || '' : '';
            const address = [street, zip, city, countryName].filter(Boolean).join(', ');
            html += `<li><strong>${name}</strong> : ${parseFloat(amount).toFixed(2)} CHF/an${address ? ' — ' + address : ''}</li>`;
        });
        html += `</ul></div>`;
    }

    // ---------- 10. Cotisation annuelle et dépôt ----------
    const membership = document.getElementById('membership_fee_amount')?.innerText || '0';
    const deposit = document.getElementById('deposit_amount')?.innerText || '0';
    html += `<div class="col-12 mt-3"><strong>🏛️ Cotisation annuelle :</strong> ${parseFloat(membership).toFixed(2)} CHF</div>`;
    html += `<div><strong>🏦 Dépôt :</strong> ${parseFloat(deposit).toFixed(2)} CHF</div>`;

    // ---------- 11. Totaux finaux ----------
    const totalMonthly = document.getElementById('recap_total_monthly')?.value || '0';
    const totalAnnual = document.getElementById('recap_total_annual')?.value || '0';
    html += `<div class="col-12 mt-2"><hr><strong>📆 TOTAL MENSUEL (écolage + parascolaire) :</strong> ${parseFloat(totalMonthly).toFixed(2)} CHF</div>`;
    html += `<div><strong>📅 TOTAL ANNUEL (tout compris) :</strong> ${parseFloat(totalAnnual).toFixed(2)} CHF</div>`;

    const discountBlock = document.getElementById('total_with_discount_block');
    if (discountBlock && discountBlock.style.display !== 'none') {
        const discountedTotal = document.getElementById('recap_total_annual_discounted')?.value || '0';
        html += `<div class="col-12 text-success"><strong>⭐ Paiement annuel anticipé (déduction 2%) : ${parseFloat(discountedTotal).toFixed(2)} CHF</strong></div>`;
    }

    // ---------- 12. Conditions et signature ----------
    const termsAccepted = form.querySelector('#terms_accepted')?.checked ? '✅ Acceptées' : '❌ Non acceptées';
    const signature = form.querySelector('#signature_text')?.value || 'Non renseignée';
    html += `<div class="col-12 mt-3"><strong>📜 Conditions générales :</strong> ${termsAccepted}</div>`;
    html += `<div><strong>✍️ Signature :</strong> ${signature}</div>`;

    html += `</div>`;
    return html;
}

// =====================================================================
// MISE À JOUR DU BLOC TARIF PROPOSÉ
// =====================================================================
function updateProposedTotal() {
    // Récupérer le montant mensuel retenu (celui affiché dans le bloc "Cas particuliers")
    const solidarityBlock = document.getElementById('final_amount_solidarity_block');
    const simpleBlock = document.getElementById('final_amount_proposal_simple_block');
    const cefBlock = document.getElementById('final_amount_proposal_cef_block');
    const standardEl = document.getElementById('final_amount_after_standard_reduction');

    let monthlyProposed = 0;

    if (solidarityBlock && solidarityBlock.style.display !== 'none') {
        const val = document.getElementById('final_amount_solidarity_value');
        monthlyProposed = val ? parseFloat(val.innerText) || 0 : 0;
    } else if (cefBlock && cefBlock.style.display !== 'none') {
        const val = document.getElementById('final_amount_proposal_cef_value');
        monthlyProposed = val ? parseFloat(val.innerText) || 0 : 0;
    } else if (simpleBlock && simpleBlock.style.display !== 'none') {
        const val = document.getElementById('final_amount_proposal_simple_value');
        monthlyProposed = val ? parseFloat(val.innerText) || 0 : 0;
    } else {
        // Standard
        monthlyProposed = standardEl ? parseFloat(standardEl.value) || 0 : 0;
    }

    // Récupérer les autres composantes (identiques au standard)
    const monthlyAfterSchool = parseFloat(document.getElementById('recap_monthly_after_school')?.value || 0);
    const membership = parseFloat(document.getElementById('recap_annual_membership')?.value || 0);
    const deposit = parseFloat(document.getElementById('recap_deposit')?.value || 0);

    // Calculs mensuels
    const monthlyTotal = monthlyProposed + monthlyAfterSchool;

    // Calculs annuels
    const annualTuition = monthlyProposed * 12;
    const annualAfter = monthlyAfterSchool * 12;
    const annualTotal = annualTuition + annualAfter + membership + deposit;

    // Mise à jour des champs du bloc "Tarif proposé"
    setVal('proposed_monthly_ecolage', monthlyProposed);
    setVal('proposed_monthly_after_school', monthlyAfterSchool);
    setVal('proposed_total_monthly', monthlyTotal);
    setVal('proposed_annual_tuition', annualTuition);
    setVal('proposed_annual_after_school', annualAfter);
    setVal('proposed_annual_membership', membership);
    setVal('proposed_deposit', deposit);
    setVal('proposed_total_annual_final', annualTotal);

    // Déduction 2% pour le tarif proposé (si applicable)
    const root = document.getElementById('ecolage_form_root');
    const paymentTerms = root ? getCheckedVal(root, 'payment_terms') : null;
    const additionalReduction = root ? getCheckedVal(root, 'additional_reduction_request') : null;
    const discountApplicable = (paymentTerms === 'annually' && additionalReduction !== '1');
    const discountBlock = document.getElementById('proposed_discount_block');
    const discountedInput = document.getElementById('proposed_total_annual_discounted');

    if (discountApplicable) {
        if (discountBlock) discountBlock.style.display = 'block';
        if (discountedInput) discountedInput.value = (annualTotal * 0.98).toFixed(2);
    } else {
        if (discountBlock) discountBlock.style.display = 'none';
    }
}

// =====================================================================
// GESTION DE LA MODALE AVEC TEMPLATE DE CONSULTATION (Ajax)
// =====================================================================
let currentModal = null;

function forceCleanupModal() {
    document.body.classList.remove('modal-open');
    document.body.style.overflow = '';
    document.documentElement.style.overflow = '';
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());
}

// Interception du bouton "Envoyer le dossier" : validation puis sauvegarde Ajax puis modale
document.addEventListener('click', function(e) {
    const btn = e.target.closest('button[name="form_action"][value="submit_dossier"]');
    if (btn && btn.closest('#ecolage_form_root')) {
        e.preventDefault();
        e.stopPropagation();
        const form = document.getElementById('ecolage_form_root');

        // Validation des champs obligatoires et formats
        const validationErrors = validateRequiredAndFormat(form);
        if (validationErrors.length > 0) {
            alert("Veuillez corriger les erreurs suivantes avant d'envoyer :\n\n- " + validationErrors.join("\n- "));
            return;
        }

        const dossierId = form.querySelector('input[name="dossier_id"]')?.value;
        if (!dossierId) {
            console.error("ID dossier manquant");
            return;
        }

        // 1) Sauvegarder le formulaire (sans quitter la page)
        const formData = new FormData(form);
        formData.set('form_action', 'save_and_stay');

        fetch(form.action || '/my/ecolage/edit/' + dossierId, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => {
            if (response.ok) {
                // 2) Après sauvegarde réussie, charger le récapitulatif mis à jour
                return fetch('/my/ecolage/dossier/' + dossierId + '/recap_html');
            } else {
                throw new Error('Sauvegarde échouée');
            }
        })
        .then(response => response.text())
        .then(html => {
            const modalBody = document.getElementById('recapModalBody');
            if (modalBody) modalBody.innerHTML = html;
            const modalElement = document.getElementById('recapModal');
            if (modalElement) {
                if (currentModal) {
                    jQuery(modalElement).modal('hide');
                    currentModal = null;
                }
                jQuery(modalElement).modal({
                    backdrop: 'static',
                    keyboard: true
                });
                jQuery(modalElement).modal('show');
                currentModal = modalElement;
            }
        })
        .catch(error => console.error('Erreur:', error));
    }
});

// Écouteur pour le bouton de confirmation dans la modale
document.addEventListener('DOMContentLoaded', function () {
    const confirmBtn = document.getElementById('confirmSubmitBtn');
    if (confirmBtn) {
        confirmBtn.addEventListener('click', function() {
            const form = document.getElementById('ecolage_form_root');
            if (form) {
                // Créer ou modifier le champ form_action
                let actionInput = form.querySelector('input[name="form_action"]');
                if (!actionInput) {
                    actionInput = document.createElement('input');
                    actionInput.type = 'hidden';
                    actionInput.name = 'form_action';
                    form.appendChild(actionInput);
                }
                actionInput.value = 'submit_dossier';
                
                // Supprimer l'ancien champ confirmed_submit si présent
                let oldConfirm = form.querySelector('input[name="confirmed_submit"]');
                if (oldConfirm) oldConfirm.remove();
                
                if (currentModal) {
                    jQuery(currentModal).modal('hide');
                    currentModal = null;
                }
                setTimeout(() => {
                    forceCleanupModal();
                    form.submit();
                }, 300);
            }
        });
    }
});

// Nettoyage après fermeture de la modale
document.addEventListener('hidden.bs.modal', function (e) {
    if (e.target.id === 'recapModal') {
        forceCleanupModal();
        if (currentModal) {
            jQuery(currentModal).modal('dispose');
            currentModal = null;
        }
    }
});

// =====================================================================
// ATTENTE DU FORMULAIRE ET INITIALISATION
// =====================================================================
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

// Toggle indépendant pour les familles liées
(function() {
    function initLinkedFamiliesToggle() {
        var checkbox = document.getElementById('toggle_linked_families');
        var block = document.getElementById('block_linked_families');
        if (checkbox && block) {
            function update() {
                block.style.display = checkbox.checked ? 'block' : 'none';
                if (!checkbox.checked) {
                    var textarea = document.querySelector('textarea[name="linked_families_comment_text"]');
                    if (textarea) textarea.value = '';
                }
            }
            checkbox.addEventListener('change', update);
            update();
        } else {
            setTimeout(initLinkedFamiliesToggle, 200);
        }
    }
    initLinkedFamiliesToggle();
})();
console.log("portal_dossier.js chargé - en attente du formulaire");