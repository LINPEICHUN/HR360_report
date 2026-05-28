/**
 * 360 度回饋分析系統 — 前端互動邏輯
 * 
 * 負責：
 * - 檔案拖曳上傳處理
 * - 表單驗證
 * - 載入動畫控制
 * - API 呼叫與報告頁面導向
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- DOM 元素 ---
    const form = document.getElementById('reportForm');
    const fileInput = document.getElementById('fileInput');
    const uploadZone = document.getElementById('uploadZone');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const removeFile = document.getElementById('removeFile');
    const submitBtn = document.getElementById('submitBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingSteps = document.getElementById('loadingSteps');
    const apiKeyToggle = document.getElementById('apiKeyToggle');
    const apiKeyInput = document.getElementById('apiKey');
    const nameInput = document.getElementById('subjectName');

    // --- API Key 顯示切換 ---
    if (apiKeyToggle) {
        apiKeyToggle.addEventListener('click', () => {
            const isPassword = apiKeyInput.type === 'password';
            apiKeyInput.type = isPassword ? 'text' : 'password';
            apiKeyToggle.textContent = isPassword ? '🔒' : '👁';
        });
    }

    // --- 檔案上傳區 ---
    // 點擊上傳
    uploadZone.addEventListener('click', (e) => {
        if (e.target === removeFile || e.target.closest('.upload-zone__remove')) return;
        fileInput.click();
    });

    // 拖曳事件
    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (isValidFile(file)) {
                // 將拖曳的檔案設定到 file input
                const dt = new DataTransfer();
                dt.items.add(file);
                fileInput.files = dt.files;
                showFileInfo(file);
            } else {
                alert('請上傳 .xlsx 或 .csv 格式的檔案。');
            }
        }
    });

    // 檔案選擇變更
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            showFileInfo(fileInput.files[0]);
        }
    });

    // 移除檔案
    removeFile.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.value = '';
        hideFileInfo();
        updateSubmitButton();
    });

    // --- 表單驗證 ---
    nameInput.addEventListener('input', updateSubmitButton);
    fileInput.addEventListener('change', updateSubmitButton);

    function updateSubmitButton() {
        const hasName = nameInput.value.trim().length > 0;
        const hasFile = fileInput.files.length > 0;
        submitBtn.disabled = !(hasName && hasFile);
    }

    // --- 表單提交 ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // 在非同步操作前先開啟新視窗，避免被瀏覽器阻擋 (Pop-up Blocker)
        const reportWindow = window.open('', '_blank');
        if (!reportWindow) {
            alert('彈出視窗被瀏覽器阻擋，請允許本網站開啟彈出視窗後再試一次。');
            return;
        }
        
        // 寫入初步的載入畫面到新視窗
        reportWindow.document.write('<!DOCTYPE html><html><head><title>產生報告中...</title><style>body{font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;background:#f8f9fa;color:#666;}</style></head><body><h2>正在為您分析並產生報告，請稍候...</h2></body></html>');
        reportWindow.document.close();

        // 顯示載入動畫
        showLoading();

        // 使用 FormData 提交
        const formData = new FormData(form);

        try {
            // 模擬進度步驟
            await simulateStep('parse', 500);
            await simulateStep('calc', 800);
            
            const apiKey = formData.get('api_key');
            if (apiKey && apiKey.trim()) {
                await simulateStep('ai', 1000);
            } else {
                markStepDone('ai');
            }

            // 實際 API 呼叫
            const response = await fetch('/api/generate-report', {
                method: 'POST',
                body: formData,
            });

            await simulateStep('render', 300);

            if (response.ok) {
                // 取得報告 HTML 並寫入剛才開啟的新視窗
                const html = await response.text();
                reportWindow.document.open();
                reportWindow.document.write(html);
                reportWindow.document.close();
            } else {
                const text = await response.text();
                reportWindow.close();
                alert('報告生成失敗，請檢查上傳的檔案格式是否正確。');
            }
        } catch (error) {
            reportWindow.close();
            alert(`發生錯誤：${error.message}`);
        } finally {
            hideLoading();
        }
    });

    // --- 輔助函式 ---
    function isValidFile(file) {
        const validTypes = [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel',
            'text/csv',
        ];
        const validExts = ['.xlsx', '.xls', '.csv'];
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        return validTypes.includes(file.type) || validExts.includes(ext);
    }

    function showFileInfo(file) {
        const size = file.size < 1024 * 1024 
            ? (file.size / 1024).toFixed(1) + ' KB'
            : (file.size / (1024 * 1024)).toFixed(1) + ' MB';
        fileName.textContent = `📄 ${file.name} (${size})`;
        fileInfo.classList.add('visible');
        updateSubmitButton();
    }

    function hideFileInfo() {
        fileInfo.classList.remove('visible');
        fileName.textContent = '';
    }

    function showLoading() {
        loadingOverlay.classList.add('active');
        // 重設步驟狀態
        loadingSteps.querySelectorAll('li').forEach(li => {
            li.classList.remove('active', 'done');
        });
    }

    function hideLoading() {
        loadingOverlay.classList.remove('active');
    }

    function simulateStep(stepName, delay) {
        return new Promise(resolve => {
            const step = loadingSteps.querySelector(`[data-step="${stepName}"]`);
            if (step) {
                step.classList.add('active');
            }
            setTimeout(() => {
                if (step) {
                    step.classList.remove('active');
                    step.classList.add('done');
                    // 加上勾號
                    step.textContent = '✅ ' + step.textContent.substring(2);
                }
                resolve();
            }, delay);
        });
    }

    function markStepDone(stepName) {
        const step = loadingSteps.querySelector(`[data-step="${stepName}"]`);
        if (step) {
            step.classList.add('done');
            step.textContent = '⏭️ ' + step.textContent.substring(2) + '（已跳過）';
        }
    }

    // --- 管理意圖備註動態更新 ---
    const purposeSelect = document.getElementById('purpose');
    const purposeNoteBox = document.getElementById('purposeNoteBox');
    const purposeNoteContent = document.getElementById('purposeNoteContent');

    const purposeNotes = {
        'IDP 發展': '<strong>🎯 IDP 發展：</strong>著重分析「自評 vs 他評」落差，深挖「盲點（自評高他評低）」與「痛點（他評或主管評分最低項）」，以推導個人中長期發展計畫。',
        '績效校準': '<strong>⚖️ 績效校準：</strong>著重比對「實際表現 vs 當前職級 KRA 期待」，明確列出尚未達標的現職行為，評估其現職符合度，作為考核依據。',
        '晉升評估': '<strong>📈 晉升評估：</strong>著重比對「實際表現 vs 下一職級 KRA 期待」，客觀衡量晉升準備度，並精確標示出 Gap Area (能力差距項目)。',
        '團隊文化': '<strong>👥 團隊文化：</strong>著重篩選與聚焦特定 Key Elements（第 3、6、8 題），剖析受評者的領導風格、團隊氛圍（心理安全感）與公司文化價值之傳遞。'
    };

    if (purposeSelect && purposeNoteContent) {
        purposeSelect.addEventListener('change', () => {
            const selectedVal = purposeSelect.value;
            const note = purposeNotes[selectedVal] || `<strong>🎯 ${selectedVal}：</strong>著重於相關面向的量化與質性回饋分析。`;
            purposeNoteContent.innerHTML = note;
            
            // 動態調整卡片外觀
            if (selectedVal === 'IDP 發展') {
                purposeNoteBox.style.borderLeftColor = '#e74c8b';
                purposeNoteBox.style.background = '#fef4f8';
            } else if (selectedVal === '績效校準') {
                purposeNoteBox.style.borderLeftColor = '#2c3e8f';
                purposeNoteBox.style.background = '#f4f6fc';
            } else if (selectedVal === '晉升評估') {
                purposeNoteBox.style.borderLeftColor = '#4a5fc1';
                purposeNoteBox.style.background = '#f8f9ff';
            } else if (selectedVal === '團隊文化') {
                purposeNoteBox.style.borderLeftColor = '#8e44ad';
                purposeNoteBox.style.background = '#faf4fc';
            } else {
                purposeNoteBox.style.borderLeftColor = '#2c3e8f';
                purposeNoteBox.style.background = '#f8f9fa';
            }
        });
        
        // 初始觸發一次以呈現預設值
        purposeSelect.dispatchEvent(new Event('change'));
    }
});
