export default async function handler(req, res) {
    if (req.method === 'POST') {
        const { type, data } = req.body;

        // Логика обработки данных
        console.log(`Received ${type} data:`, data);

        // Пример исправленного ответа
        res.status(200).json({ success: true }); // JSON.stringify уже встроен
    } else {
        res.status(405).send(JSON.stringify({ error: 'Method Not Allowed' })); // Преобразование ошибки в строку
    }
}
