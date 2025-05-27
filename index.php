<?php
// Função para pegar o conteúdo HTML da URL e extrair os links dos arquivos de mídia
function getMediaLinks($url) {
    // Usando cURL para obter o conteúdo da página
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    $content = curl_exec($ch);
    curl_close($ch);

    // Verifica se o conteúdo foi recuperado com sucesso
    if (!$content) {
        return "Erro ao acessar a página.";
    }

    // Usando expressão regular para capturar links de arquivos de mídia (sem áudio)
    $mediaLinks = [];
    preg_match_all('/(?:src|href)="(https?:\/\/[^"]*\.(?:mp4|webm|ogg|png|jpg|jpeg|gif|webp|bmp|flv|avi))"/i', $content, $matches);

    // Adiciona todos os links encontrados à lista
    foreach ($matches[1] as $link) {
        $mediaLinks[] = $link;
    }

    return $mediaLinks;
}

// Função para exibir visualizações de imagens (se for imagem)
function displayImagePreview($url) {
    $image = getimagesize($url);
    return $image ? "<img src='$url' alt='Imagem' style='max-width: 200px; margin: 10px;'>" : '';
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $url = $_POST['url'] ?? '';

    if (empty($url)) {
        $errorMessage = "Por favor, insira um URL.";
    } else {
        // Pegando os links de mídia do site
        $mediaLinks = getMediaLinks($url);
    }
}

?>

<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scraper de Mídia</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        form { margin-bottom: 20px; }
        .media-item { margin-bottom: 15px; }
        .video { margin-top: 10px; }
    </style>
</head>
<body>

    <h1>Extrair Links de Mídia</h1>
    <form method="POST">
        <label for="url">Informe a URL do site:</label>
        <input type="text" id="url" name="url" value="<?= htmlspecialchars($url ?? '') ?>" required>
        <button type="submit">Buscar Links</button>
    </form>

    <?php if (!empty($errorMessage)): ?>
        <p style="color: red;"><?= $errorMessage ?></p>
    <?php endif; ?>

    <?php if (isset($mediaLinks)): ?>
        <?php if (empty($mediaLinks)): ?>
            <p>Nenhum arquivo de mídia encontrado.</p>
        <?php else: ?>
            <h2>Links Encontrados:</h2>
            <ul>
                <?php foreach ($mediaLinks as $link): ?>
                    <li class="media-item">
                        <strong>Link:</strong> <a href="<?= $link ?>" target="_blank"><?= $link ?></a><br>
                        <?php if (preg_match('/\.(png|jpg|jpeg|gif|webp|bmp)$/i', $link)): ?>
                            <div class="image-preview">
                                <?= displayImagePreview($link) ?>
                            </div>
                        <?php elseif (preg_match('/\.(mp4|webm|ogg|flv|avi)$/i', $link)): ?>
                            <div class="video">
                                <strong>Vídeo:</strong><br>
                                <video width="320" height="240" controls>
                                    <source src="<?= $link ?>" type="video/<?= pathinfo($link, PATHINFO_EXTENSION) ?>">
                                    Seu navegador não suporta a tag de vídeo.
                                </video>
                            </div>
                        <?php endif; ?>
                    </li>
                <?php endforeach; ?>
            </ul>
        <?php endif; ?>
    <?php endif; ?>

</body>
</html>