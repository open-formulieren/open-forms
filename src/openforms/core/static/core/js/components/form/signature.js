export const signature = `
<aside class="signature">
    {{ctx.element}}
    <div class="signature__body" style="width: {{ctx.component.width}};height: {{ctx.component.height}}; tabindex="{{ctx.component.tabindex || 0}}" ref="padBody">
        <i class="fa-icon {{ctx.iconClass('refresh')}}" ref="refresh"></i>
        <canvas class="signature-pad-canvas" height="{{ctx.component.height}}" ref="canvas"></canvas>    
        <img ref="signatureImage">
    </div>
    
    {% if (ctx.component.footer) { %}
    <footer class="signature__footer">
        <p class="body body--muted">{{ctx.t(ctx.component.footer)}}</p>
    </footer>
</aside>
{% } %}
`;
