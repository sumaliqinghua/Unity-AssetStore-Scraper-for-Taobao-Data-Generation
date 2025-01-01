document.addEventListener('DOMContentLoaded', function() {
    // 标签切换功能
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // 移除所有active类
            tabs.forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // 添加active类到当前标签
            tab.classList.add('active');
            const tabId = tab.getAttribute('data-tab');
            document.getElementById(tabId + '-tab').classList.add('active');
        });
    });

    // 加载已保存的配置
    chrome.storage.sync.get([
        'titleContent',
        'price',
        'detailContent',
        'imagePath',
        'confirmSelector',
        'titleSelector',
        'priceSelector',
        'stockSelector',
        'shipTimeSelector',
        'textButtonSelector',
        'detailEditorSelector',
        'detailContentSelector',
        'imageUploadSelector'
    ], function(result) {
        // 内容配置
        document.getElementById('titleContent').value = result.titleContent || '';
        document.getElementById('price').value = result.price || '';
        document.getElementById('detailContent').value = result.detailContent || '';
        document.getElementById('imagePath').value = result.imagePath || '';

        // 选择器配置
        document.getElementById('confirmSelector').value = result.confirmSelector || '.next-btn-helper';
        document.getElementById('titleSelector').value = result.titleSelector || '.next-input.next-input-single.next-input-medium[name="title"]';
        document.getElementById('priceSelector').value = result.priceSelector || 'input[name="price"]';
        document.getElementById('stockSelector').value = result.stockSelector || 'input[name="quantity"]';
        document.getElementById('shipTimeSelector').value = result.shipTimeSelector || 'input[value="24"]';
        document.getElementById('textButtonSelector').value = result.textButtonSelector || 'button:contains("文字")';
        document.getElementById('detailEditorSelector').value = result.detailEditorSelector || '.detail-text-editor';
        document.getElementById('detailContentSelector').value = result.detailContentSelector || '.detail-text-editor';
        document.getElementById('imageUploadSelector').value = result.imageUploadSelector || '.next-upload-select';
    });

    // 保存配置按钮事件
    document.getElementById('saveConfig').addEventListener('click', function() {
        const config = {
            // 内容配置
            titleContent: document.getElementById('titleContent').value,
            price: document.getElementById('price').value,
            detailContent: document.getElementById('detailContent').value,
            imagePath: document.getElementById('imagePath').value,
            // 选择器配置
            confirmSelector: document.getElementById('confirmSelector').value,
            titleSelector: document.getElementById('titleSelector').value,
            priceSelector: document.getElementById('priceSelector').value,
            stockSelector: document.getElementById('stockSelector').value,
            shipTimeSelector: document.getElementById('shipTimeSelector').value,
            textButtonSelector: document.getElementById('textButtonSelector').value,
            detailEditorSelector: document.getElementById('detailEditorSelector').value,
            detailContentSelector: document.getElementById('detailContentSelector').value,
            imageUploadSelector: document.getElementById('imageUploadSelector').value
        };

        chrome.storage.sync.set(config, function() {
            alert('配置已保存！');
        });
    });

    // 填充内容按钮事件
    document.getElementById('fillContent').addEventListener('click', async function() {
        try {
            // 获取当前标签页
            const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
            
            if (!tab) {
                throw new Error('未能获取当前标签页');
            }

            // 检查是否在正确的域名下
            if (!tab.url.includes('taobao.com')) {
                alert('请先打开淘宝卖家页面！');
                return;
            }

            // 注入content script
            await chrome.scripting.executeScript({
                target: {tabId: tab.id},
                files: ['content.js']
            });

            // 发送消息到content script
            const response = await chrome.tabs.sendMessage(tab.id, {
                action: 'fillContent',
                config: {
                    // 内容配置
                    titleContent: document.getElementById('titleContent').value,
                    price: document.getElementById('price').value,
                    detailContent: document.getElementById('detailContent').value,
                    imagePath: document.getElementById('imagePath').value,
                    // 选择器配置
                    confirmSelector: document.getElementById('confirmSelector').value,
                    titleSelector: document.getElementById('titleSelector').value,
                    priceSelector: document.getElementById('priceSelector').value,
                    stockSelector: document.getElementById('stockSelector').value,
                    shipTimeSelector: document.getElementById('shipTimeSelector').value,
                    textButtonSelector: document.getElementById('textButtonSelector').value,
                    detailEditorSelector: document.getElementById('detailEditorSelector').value,
                    detailContentSelector: document.getElementById('detailContentSelector').value,
                    imageUploadSelector: document.getElementById('imageUploadSelector').value
                }
            });

            console.log('消息发送成功:', response);
        } catch (error) {
            console.error('错误:', error);
            alert('发生错误: ' + error.message + '\n请刷新页面后重试');
        }
    });
});
