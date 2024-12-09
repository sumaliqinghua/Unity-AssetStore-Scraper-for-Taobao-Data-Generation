// 监听来自popup的消息
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
    if (request.action === 'fillContent') {
        const config = request.config;
        
        // 填充标题
        if (config.titleSelector && config.titleContent) {
            const titleElement = document.querySelector(config.titleSelector);
            if (titleElement) {
                titleElement.value = config.titleContent;
                // 触发input事件以确保值更新
                titleElement.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }

        // 填充内容
        if (config.contentSelector && config.detailContent) {
            const contentElement = document.querySelector(config.contentSelector);
            if (contentElement) {
                contentElement.value = config.detailContent;
                contentElement.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }

        // 处理图片上传
        if (config.imageSelector && config.imagePath) {
            const imageButton = document.querySelector(config.imageSelector);
            if (imageButton) {
                // 注意：由于浏览器安全限制，直接访问本地文件路径可能不被允许
                // 这里需要通过点击触发文件选择对话框
                imageButton.click();
                // 提示用户手动选择文件
                alert('请在弹出的文件选择框中选择图片：' + config.imagePath);
            }
        }
    }
});
