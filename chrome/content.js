// 获取元素的选择器
function getSelector(element) {
    // 获取所有可能的属性
    function getAllAttributes(el) {
        const attrs = el.attributes;
        let result = [];
        for (let i = 0; i < attrs.length; i++) {
            const attr = attrs[i];
            // 忽略一些动态或不稳定的属性
            if (!['style', 'data-spm', 'data-spm-anchor-id'].includes(attr.name)) {
                result.push(`[${attr.name}="${attr.value}"]`);
            }
        }
        return result;
    }

    // 获取元素的完整选择器
    function getFullSelector(el) {
        if (el.id) {
            return '#' + el.id;
        }
        
        let path = [];
        while (el) {
            let selector = el.tagName.toLowerCase();
            let parent = el.parentElement;
            
            if (parent) {
                let children = parent.children;
                let index = Array.from(children).indexOf(el) + 1;
                selector += `:nth-child(${index})`;
            }
            
            path.unshift(selector);
            el = parent;
        }
        
        return path.join(' > ');
    }

    // 获取父元素的选择器（最多往上查找3层）
    function getParentSelectors(el, maxLevels = 3) {
        let selectors = [];
        let current = el;
        let level = 0;
        
        while (current.parentElement && level < maxLevels) {
            const parentSelector = getFullSelector(current.parentElement);
            if (parentSelector) {
                selectors.unshift(parentSelector);
            }
            current = current.parentElement;
            level++;
        }
        
        return selectors;
    }

    // 生成多个可能的选择器组合
    function generateSelectors(el) {
        const selectors = [];
        const fullSelector = getFullSelector(el);
        const parentSelectors = getParentSelectors(el);
        
        // 1. 完整的选择器（包含所有属性）
        selectors.push(fullSelector);
        
        // 2. 带一层父元素的选择器
        if (parentSelectors.length > 0) {
            selectors.push(`${parentSelectors[parentSelectors.length - 1]} > ${fullSelector}`);
        }
        
        // 3. 带所有父元素的选择器
        if (parentSelectors.length > 0) {
            selectors.push(`${parentSelectors.join(' ')} > ${fullSelector}`);
        }
        
        return selectors;
    }

    // 测试选择器的唯一性
    function testSelector(selector) {
        try {
            const elements = document.querySelectorAll(selector);
            return elements.length === 1 ? selector : null;
        } catch (e) {
            return null;
        }
    }

    // 获取最佳选择器
    const selectors = generateSelectors(element);
    for (const selector of selectors) {
        const validSelector = testSelector(selector);
        if (validSelector) {
            return validSelector;
        }
    }

    // 如果没有找到唯一的选择器，返回完整路径
    return selectors[selectors.length - 1];
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
                    max-width: 80%;
                    word-break: break-all;
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
                console.log('开始填充内容，配置:', config);

                // 填充标题
                const titleInput = document.querySelector(config.titleSelector);
                console.log('标题输入框:', titleInput, '选择器:', config.titleSelector);
                if (titleInput && config.titleContent) {
                    titleInput.value = config.titleContent;
                    titleInput.dispatchEvent(new Event('input', { bubbles: true }));
                    console.log('标题已填充');
                    // 触发change事件
                    titleInput.dispatchEvent(new Event('change', { bubbles: true }));
                }

                // 填充价格
                const priceInput = document.querySelector(config.priceSelector);
                console.log('价格输入框:', priceInput, '选择器:', config.priceSelector);
                if (priceInput && config.price) {
                    priceInput.value = config.price;
                    priceInput.dispatchEvent(new Event('input', { bubbles: true }));
                    console.log('价格已填充');
                    // 触发change事件
                    priceInput.dispatchEvent(new Event('change', { bubbles: true }));
                }

                // 填充库存
                const stockInput = document.querySelector(config.stockSelector);
                console.log('库存输入框:', stockInput, '选择器:', config.stockSelector);
                if (stockInput) {
                    stockInput.value = "9999";
                    stockInput.dispatchEvent(new Event('input', { bubbles: true }));
                    console.log('库存已填充');
                    // 触发change事件
                    stockInput.dispatchEvent(new Event('change', { bubbles: true }));
                }

                // 选择24小时发货
                const shipTimeRadio = document.querySelector(config.shipTimeSelector);
                console.log('发货时间选择框:', shipTimeRadio, '选择器:', config.shipTimeSelector);
                if (shipTimeRadio) {
                    shipTimeRadio.click();
                    console.log('已选择24小时发货');
                }

                // 点击文字按钮并填写详情
                const textButton = document.querySelector(config.textButtonSelector);
                console.log('文字按钮:', textButton, '选择器:', config.textButtonSelector);
                if (textButton) {
                    textButton.click();
                    console.log('已点击文字按钮');
                    // 等待文本模块加载
                    setTimeout(() => {
                        const detailTextArea = document.querySelector(config.detailEditorSelector);
                        console.log('详情编辑器:', detailTextArea, '选择器:', config.detailEditorSelector);
                        if (detailTextArea && config.detailContent) {
                            // 模拟双击
                            detailTextArea.dispatchEvent(new MouseEvent('dblclick', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            }));
                            console.log('已双击详情编辑器');
                            
                            // // 等待编辑器完全打开
                            // setTimeout(() => {
                            //     const editor = document.querySelector(config.detailEditorSelector + ' textarea');
                            //     console.log('详情文本框:', editor);
                            //     if (editor) {
                            //         editor.value = config.detailContent;
                            //         editor.dispatchEvent(new Event('input', { bubbles: true }));
                            //         // 触发change事件
                            //         editor.dispatchEvent(new Event('change', { bubbles: true }));
                            //         console.log('详情内容已填充');
                            //     }
                            // }, 1000);
                        }
                    }, 1000);
                }

                // 处理图片上传
                const imageUploadButton = document.querySelector(config.imageUploadSelector);
                console.log('图片上传按钮:', imageUploadButton, '选择器:', config.imageUploadSelector);
                if (imageUploadButton && config.imagePath) {
                    imageUploadButton.click();
                    console.log('已点击图片上传按钮');
                    // 提示用户手动选择文件
                    alert('请在弹出的文件选择框中选择图片：' + config.imagePath);
                }
            } catch (error) {
                console.error('填充内容时发生错误:', error);
                alert('填充内容时发生错误: ' + error.message);
            }
        }, 2000); // 增加等待时间到2秒
    } else if (request.action === 'enableSelectorCopy') {
        enableSelectorCopy();
    }
});

// 自动启用选择器复制功能
enableSelectorCopy();
