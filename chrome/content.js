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
    }
});
