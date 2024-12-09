// 获取元素的选择器
function getSelector(element) {
    if (element.id) {
        return '#' + element.id;
    }
    
    if (element.className) {
        const classes = Array.from(element.classList).join('.');
        return '.' + classes;
    }

    let selector = element.tagName.toLowerCase();
    if (element.name) {
        selector += `[name="${element.name}"]`;
    }
    
    // 添加其他可能有用的属性
    if (element.type) {
        selector += `[type="${element.type}"]`;
    }
    if (element.value) {
        selector += `[value="${element.value}"]`;
    }
    
    return selector;
}

// 添加选择器复制功能
function enableSelectorCopy() {
    document.addEventListener('click', function(e) {
        if (e.altKey) {  // 只在按住Alt键时触发
            e.preventDefault();
            const selector = getSelector(e.target);
            // 复制到剪贴板
            navigator.clipboard.writeText(selector).then(() => {
                // 显示提示
                const tip = document.createElement('div');
                tip.textContent = `已复制选择器: ${selector}`;
                tip.style.cssText = `
                    position: fixed;
                    top: 10px;
                    right: 10px;
                    background: #4CAF50;
                    color: white;
                    padding: 10px;
                    border-radius: 4px;
                    z-index: 10000;
                `;
                document.body.appendChild(tip);
                setTimeout(() => tip.remove(), 3000);
            });
        }
    });
}

// 监听来自popup的消息
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === 'fillContent') {
        const config = request.config;
        
        // 检查当前页面URL，如果在分类选择页面，点击确认按钮
        if (window.location.href.includes('category.htm')) {
            const confirmButton = document.querySelector(config.confirmSelector);
            if (confirmButton) {
                confirmButton.click();
                return;
            }
        }

        // 等待页面元素加载
        setTimeout(async function() {
            try {
                // 填充标题
                const titleInput = document.querySelector(config.titleSelector);
                if (titleInput && config.titleContent) {
                    titleInput.value = config.titleContent;
                    titleInput.dispatchEvent(new Event('input', { bubbles: true }));
                }

                // 填充价格
                const priceInput = document.querySelector(config.priceSelector);
                if (priceInput && config.price) {
                    priceInput.value = config.price;
                    priceInput.dispatchEvent(new Event('input', { bubbles: true }));
                }

                // 填充库存
                const stockInput = document.querySelector(config.stockSelector);
                if (stockInput) {
                    stockInput.value = "9999";
                    stockInput.dispatchEvent(new Event('input', { bubbles: true }));
                }

                // 选择24小时发货
                const shipTimeRadio = document.querySelector(config.shipTimeSelector);
                if (shipTimeRadio) {
                    shipTimeRadio.click();
                }

                // 点击文字按钮并填写详情
                const textButton = document.querySelector(config.textButtonSelector);
                if (textButton) {
                    textButton.click();
                    // 等待文本模块加载
                    setTimeout(() => {
                        const detailTextArea = document.querySelector(config.detailEditorSelector);
                        if (detailTextArea && config.detailContent) {
                            // 模拟双击
                            detailTextArea.dispatchEvent(new MouseEvent('dblclick', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            }));
                            
                            // 等待编辑器完全打开
                            setTimeout(() => {
                                const editor = document.querySelector(config.detailEditorSelector + ' textarea');
                                if (editor) {
                                    editor.value = config.detailContent;
                                    editor.dispatchEvent(new Event('input', { bubbles: true }));
                                }
                            }, 500);
                        }
                    }, 500);
                }

                // 处理图片上传
                const imageUploadButton = document.querySelector(config.imageUploadSelector);
                if (imageUploadButton && config.imagePath) {
                    imageUploadButton.click();
                    // 提示用户手动选择文件
                    alert('请在弹出的文件选择框中选择图片：' + config.imagePath);
                }
            } catch (error) {
                console.error('填充内容时发生错误:', error);
                alert('填充内容时发生错误: ' + error.message);
            }
        }, 1000);
    } else if (request.action === 'enableSelectorCopy') {
        enableSelectorCopy();
    }
});

// 自动启用选择器复制功能
enableSelectorCopy();
