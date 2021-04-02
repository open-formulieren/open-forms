export const getTemplate = () => {
    return `
        <div class="message message--{{ctx.level}}">{{ctx.message}}</div>
    `;
};
