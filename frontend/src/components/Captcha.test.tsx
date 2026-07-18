import { render } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { Captcha } from './Captcha'

describe('Captcha', () => {
  it('auto-resolves with the dev placeholder token when no site key is configured', () => {
    const onToken = vi.fn()
    const { container } = render(<Captcha onToken={onToken} />)

    expect(onToken).toHaveBeenCalledWith('dev-mode-no-turnstile-configured')
    expect(container).toBeEmptyDOMElement()
  })
})
