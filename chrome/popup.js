document.addEventListener('DOMContentLoaded', function() {
    // 加载已保存的配置
    chrome.storage.sync.get([
        'titleContent',
        'price',
        'detailContent',
        'imagePath'
    ], function(result) {
        document.getElementById('titleContent').value = result.titleContent || '';
        document.getElementById('price').value = result.price || '';
        document.getElementById('detailContent').value = result.detailContent || '';
        document.getElementById('imagePath').value = result.imagePath || '';
    });

    // 保存配置按钮事件
    document.getElementById('saveConfig').addEventListener('click', function() {
        const config = {
            titleContent: document.getElementById('titleContent').value,
            price: document.getElementById('price').value,
            detailContent: document.getElementById('detailContent').value,
            imagePath: document.getElementById('imagePath').value
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
                    titleContent: document.getElementById('titleContent').value,
                    price: document.getElementById('price').value,
                    detailContent: document.getElementById('detailContent').value,
                    imagePath: document.getElementById('imagePath').value
                }
            });

            console.log('消息发送成功:', response);
        } catch (error) {
            console.error('错误:', error);
            alert('发生错误: ' + error.message + '\n请刷新页面后重试');
        }
    });
});
