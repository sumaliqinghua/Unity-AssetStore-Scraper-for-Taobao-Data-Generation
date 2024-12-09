document.addEventListener('DOMContentLoaded', function() {
    // 加载已保存的配置
    chrome.storage.sync.get([
        'titleSelector',
        'contentSelector',
        'imageSelector',
        'titleContent',
        'detailContent',
        'imagePath'
    ], function(result) {
        document.getElementById('titleSelector').value = result.titleSelector || '';
        document.getElementById('contentSelector').value = result.contentSelector || '';
        document.getElementById('imageSelector').value = result.imageSelector || '';
        document.getElementById('titleContent').value = result.titleContent || '';
        document.getElementById('detailContent').value = result.detailContent || '';
        document.getElementById('imagePath').value = result.imagePath || '';
    });

    // 保存配置按钮事件
    document.getElementById('saveConfig').addEventListener('click', function() {
        const config = {
            titleSelector: document.getElementById('titleSelector').value,
            contentSelector: document.getElementById('contentSelector').value,
            imageSelector: document.getElementById('imageSelector').value,
            titleContent: document.getElementById('titleContent').value,
            detailContent: document.getElementById('detailContent').value,
            imagePath: document.getElementById('imagePath').value
        };

        chrome.storage.sync.set(config, function() {
            alert('配置已保存！');
        });
    });

    // 填充内容按钮事件
    document.getElementById('fillContent').addEventListener('click', function() {
        chrome.tabs.query({active: true, currentWindow: true}, function(tabs) {
            chrome.tabs.sendMessage(tabs[0].id, {
                action: 'fillContent',
                config: {
                    titleSelector: document.getElementById('titleSelector').value,
                    contentSelector: document.getElementById('contentSelector').value,
                    imageSelector: document.getElementById('imageSelector').value,
                    titleContent: document.getElementById('titleContent').value,
                    detailContent: document.getElementById('detailContent').value,
                    imagePath: document.getElementById('imagePath').value
                }
            });
        });
    });
});
