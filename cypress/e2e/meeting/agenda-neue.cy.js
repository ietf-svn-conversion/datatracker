import { DateTime } from 'luxon'
import path from 'path'
import { isEqual } from 'lodash-es'
import meetingGenerator from '../../generators/meeting'

const viewports = {
  desktop: [1536, 960],
  smallDesktop: [1280, 800],
  tablet: [768, 1024],
  mobile: [360, 760]
}

const injectMeetingData = (win, meetingNumber) => {
  const meetingDataScript = win.document.createElement('script')
  meetingDataScript.id = 'meeting-data'
  meetingDataScript.type = 'application/json'
  meetingDataScript.innerHTML = `{"meetingNumber": "${meetingNumber}"}`
  win.document.querySelector('head').appendChild(meetingDataScript)
}

// ====================================================================
// AGENDA-NEUE (past meeting) | DESKTOP viewport
// ====================================================================

describe('meeting -> agenda-neue [past, desktop]', {
    viewportWidth: viewports.desktop[0],
    viewportHeight: viewports.desktop[1]
  }, () => {
  const meetingData = meetingGenerator.generateAgendaResponse({ future: false })

  before(() => {
    cy.intercept('GET', `/api/meeting/${meetingData.meeting.number}/agenda-data`, { body: meetingData }).as('getMeetingData')
    cy.visit(`/meeting/${meetingData.meeting.number}/agenda-neue`, {
      onBeforeLoad: (win) => { injectMeetingData(win, meetingData.meeting.number) }
    })
    cy.wait('@getMeetingData')
  })

  // -> HEADER

  it(`has IETF ${meetingData.meeting.number} title`, () => {
    cy.get('.agenda h1').first().contains(`IETF ${meetingData.meeting.number} Meeting Agenda`)
  })
  it(`has meeting city subtitle`, () => {
    cy.get('.agenda h4').first().contains(meetingData.meeting.city)
  })
  it(`has meeting date subtitle`, () => {
    cy.get('.agenda h4').first().contains(/[a-zA-Z] [0-9]{1,2} - ([a-zA-Z]+ )?[0-9]{1,2}, [0-9]{4}/i)
  })
  it(`has meeting last updated datetime`, () => {
    const updatedDateTime = DateTime.fromISO(meetingData.meeting.updated).setZone(meetingData.meeting.timezone).toFormat(`DD 'at' tt ZZZZ`)
    cy.get('.agenda h6').first().contains(updatedDateTime)
  })

  // -> NAV

  it(`has the correct navigation items`, () => {
    cy.get('.agenda .meeting-nav > li').should('have.length', 3)
    cy.get('.agenda .meeting-nav > li').first().contains('Agenda')
    cy.get('.agenda .meeting-nav > li').eq(1).contains('Floor plan')
    cy.get('.agenda .meeting-nav > li').last().contains('Plaintext')
  })
  it(`has the Settings button on the right`, () => {
    cy.get('.agenda .meeting-nav').next('button').should('exist')
      .and('include.text', 'Settings')
    cy.window().then(win => {
      cy.get('.agenda .meeting-nav').next('button').then(el => {
        const btnBounds = el[0].getBoundingClientRect()
        expect(btnBounds.x).to.be.greaterThan(win.innerWidth - btnBounds.width - 100)
      })
    })
  })

  // -> SCHEDULE LIST -> Header

  it(`has schedule list title`, () => {
    cy.get('.agenda h2').first().contains(`Schedule`)
  })
  it(`has info note`, () => {
    cy.get('.agenda .agenda-infonote').should('exist').and('include.text', meetingData.meeting.infoNote)
  })
  it(`info note can be dismissed / reopened`, () => {
    cy.get('.agenda .agenda-infonote > button').click()
    cy.get('.agenda .agenda-infonote').should('not.exist')
    cy.get('.agenda h2').first().next('button').should('exist')
    cy.get('.agenda h2').first().next('button').click()
    cy.get('.agenda .agenda-infonote').should('exist')
    cy.get('.agenda h2').first().next('button').should('not.exist')
  })
  it(`has timezone selector`, () => {
    cy.get('.agenda .agenda-tz-selector').should('exist')
    cy.get('.agenda .agenda-tz-selector').prev().should('exist').and('include.text', 'Timezone:').prev('.bi').should('exist')
    cy.get('.agenda .agenda-tz-selector > button').should('have.length', 3)
    cy.get('.agenda .agenda-tz-selector > button').first().contains('Meeting')
    cy.get('.agenda .agenda-tz-selector > button').eq(1).contains('Local')
    cy.get('.agenda .agenda-tz-selector > button').last().contains('UTC')
    cy.get('.agenda .agenda-timezone-ddn').should('exist')
  })
  it('can change timezone', () => {
    // Switch to local timezone
    cy.get('.agenda .agenda-tz-selector > button').eq(1).click().should('have.class', 'n-button--primary-type')
      .prev('button').should('not.have.class', 'n-button--primary-type')
    const localDateTime = DateTime.fromISO(meetingData.meeting.updated).setZone('local').toFormat(`DD 'at' tt ZZZZ`)
    cy.get('.agenda h6').first().contains(localDateTime)
    // Switch to UTC
    cy.get('.agenda .agenda-tz-selector > button').last().click().should('have.class', 'n-button--primary-type')
      .prev('button').should('not.have.class', 'n-button--primary-type')
    const utcDateTime = DateTime.fromISO(meetingData.meeting.updated).setZone('utc').toFormat(`DD 'at' tt ZZZZ`)
    cy.get('.agenda h6').first().contains(utcDateTime)
    cy.get('.agenda .agenda-timezone-ddn').contains('UTC')
    // Switch back to meeting timezone
    cy.get('.agenda .agenda-tz-selector > button').first().click().should('have.class', 'n-button--primary-type')
    cy.get('.agenda .agenda-timezone-ddn').contains('Tokyo')
  })

  // -> FILTER BY AREA/GROUP DIALOG

  it('can filter by area/group', () => {
    // Open dialog
    cy.get('#agenda-quickaccess-filterbyareagroups-btn').should('exist').and('be.visible').click()
    cy.get('.agenda-personalize').should('exist').and('be.visible')
    // Check header elements
    cy.get('.agenda-personalize .n-drawer-header__main > span').contains('Filter Areas + Groups')
    cy.get('.agenda-personalize .agenda-personalize-actions > button').should('have.length', 3)
    cy.get('.agenda-personalize .agenda-personalize-actions > button').first().contains('Clear Selection')
    cy.get('.agenda-personalize .agenda-personalize-actions > button').eq(1).contains('Cancel')
    cy.get('.agenda-personalize .agenda-personalize-actions > button').last().contains('Apply')
    // Check categories
    cy.get('.agenda-personalize .agenda-personalize-category').should('have.length', meetingData.categories.length)
    // Check areas + groups
    cy.get('.agenda-personalize .agenda-personalize-category').each((el, idx) => {
      const cat = meetingData.categories[idx]
      cy.wrap(el).find('.agenda-personalize-area').should('have.length', cat.length)
        .each((areaEl, areaIdx) => {
          // Area Button
          const area = cat[areaIdx]
          cy.wrap(areaEl).find('.agenda-personalize-areamain').scrollIntoView()
          if (area.label) {
            cy.wrap(areaEl).find('.agenda-personalize-areamain > button').should('be.visible').contains(area.label)
          } else {
            cy.wrap(areaEl).find('.agenda-personalize-areamain > button').should('not.exist')
          }
          // Group Buttons
          cy.wrap(areaEl).find('.agenda-personalize-groups > button').should('have.length', area.children.length)
            .each((groupEl, groupIdx) => {
              const group = area.children[groupIdx]
              cy.wrap(groupEl).should('be.visible').contains(group.label)
              if (group.is_bof) {
                cy.wrap(groupEl).should('have.class', 'is-bof')
                cy.wrap(groupEl).find('.badge').should('be.visible').contains('BoF')
              }
            })
          // Test Area Selection
          if (area.label) {
            cy.wrap(areaEl).find('.agenda-personalize-areamain > button').click()
            cy.wrap(areaEl).find('.agenda-personalize-groups > button').should('have.class', 'is-checked')
            cy.wrap(areaEl).find('.agenda-personalize-areamain > button').click()
            cy.wrap(areaEl).find('.agenda-personalize-groups > button').should('not.have.class', 'is-checked')
          }
          // Test Group Selection
          cy.wrap(areaEl).find('.agenda-personalize-groups > button').any().click()
            .should('have.class', 'is-checked').click().should('not.have.class', 'is-checked')
        })
    })
    // Test multi-toggled_by button trigger
    cy.get(`.agenda-personalize .agenda-personalize-category:last .agenda-personalize-area:last .agenda-personalize-groups > button:contains('BoF')`).as('bofbtn')
    cy.get('@bofbtn').click()
    cy.get('.agenda-personalize .agenda-personalize-group:has(.badge)').should('have.class', 'is-checked')
    cy.get('@bofbtn').click()
    cy.get('.agenda-personalize .agenda-personalize-group:has(.badge)').should('not.have.class', 'is-checked')
    // Clicking all groups from area then area button should unselect all
    cy.get('.agenda-personalize .agenda-personalize-area:first .agenda-personalize-groups > button').click({ multiple: true })
    cy.get('.agenda-personalize .agenda-personalize-area:first .agenda-personalize-areamain > button').click()
    cy.get('.agenda-personalize .agenda-personalize-area:first .agenda-personalize-groups > button').should('not.have.class', 'is-checked')
    // Test Clear Selection
    cy.get('.agenda-personalize .agenda-personalize-group').any(10).click({ multiple: true })
    cy.get('.agenda-personalize .agenda-personalize-actions > button').first().click()
    cy.get('.agenda-personalize .agenda-personalize-group').should('not.have.class', 'is-checked')
    // Click Cancel should hide dialog
    cy.get('.agenda-personalize .agenda-personalize-actions > button').eq(1).click()
    cy.get('.agenda-personalize').should('not.exist')
  })

  // -> FILTER BY AREA/GROUP DIALOG

  it.only('can export / import settings', () => {
    // Open dialog
    cy.get('.meeting-nav').next('button').should('exist').and('be.visible').click()
    cy.get('.agenda-settings').should('exist').and('be.visible')
    // Check header elements
    cy.get('.agenda-settings .n-drawer-header__main > span').contains('Agenda Settings')
    cy.get('.agenda-settings .agenda-settings-actions > button').should('have.length', 2)
    cy.get('.agenda-settings .agenda-settings-actions > button').first().should('be.visible')
    cy.get('.agenda-settings .agenda-settings-actions > button').last().contains('Close')
    // Check timezone controls
    cy.get('.agenda-settings-content > .n-divider:first').contains('Timezone')
    // Check export config
    cy.get('.agenda-settings .agenda-settings-actions > button').first().click()
    cy.get('.n-dropdown-option:contains("Export Configuration")').should('exist').and('be.visible').click()
    cy.readFile(path.join(Cypress.config('downloadsFolder'), 'agenda-settings.json'), { timeout: 15000 }).then(cfg => {
      cy.fixture('agenda-settings.json').then(cfgValid => {
        expect(isEqual(cfg, cfgValid)).to.be.true
      })
    })
    // Check import config
    cy.fixture('agenda-settings.json', { encoding: 'utf8' }).then(cfgImport => {
      // Stub the native file picker
      // From https://cypresstips.substack.com/p/stub-the-browser-filesystem-api
      cy.window().then((win) => {
        cy.stub(win, 'showOpenFilePicker').resolves([{
          getFile: cy.stub().resolves({
            text: cy.stub().resolves(JSON.stringify(cfgImport))
          })
        }])
        cy.get('.agenda-settings .agenda-settings-actions > button').first().click()
        cy.get('.n-dropdown-option:contains("Import Configuration")').should('exist').and('be.visible').click()
        cy.get('.n-message').should('contain', 'Config imported successfully')
      })
    })
    // Click Close should hide dialog
    cy.get('.agenda-settings .agenda-settings-actions > button').last().click()
    cy.get('.agenda-settings').should('not.exist')
  })
})

// ====================================================================
// AGENDA-NEUE (future meeting) | DESKTOP viewport
// ====================================================================

describe('meeting -> agenda-neue [future, desktop]', {
    viewportWidth: viewports.desktop[0],
    viewportHeight: viewports.desktop[1]
  }, () => {
  const meetingData = meetingGenerator.generateAgendaResponse({ future: true })

  before(() => {
    cy.intercept('GET', `/api/meeting/${meetingData.meeting.number}/agenda-data`, { body: meetingData }).as('getMeetingData')
    cy.visit(`/meeting/${meetingData.meeting.number}/agenda-neue`, {
      onBeforeLoad: (win) => { injectMeetingData(win, meetingData.meeting.number) }
    })
    cy.wait('@getMeetingData')
  })

  // -> SCHEDULE LIST

  it(`has current meeting warning`, () => {
    cy.get('.agenda .agenda-currentwarn').should('exist').and('include.text', 'Note: IETF agendas are subject to change, up to and during a meeting.')
  })
})

// ====================================================================
// FLOOR-PLAN-NEUE | All Viewports
// ====================================================================

describe(`meeting -> floor-plan-neue`, () => {
  for (const vp of ['desktop', 'smallDesktop', 'tablet', 'mobile']) {
    describe(vp, {
        viewportWidth: viewports[vp][0],
        viewportHeight: viewports[vp][1]
      }, () => {
      const meetingData = meetingGenerator.generateAgendaResponse({ skipSchedule: true })

      before(() => {
        cy.intercept('GET', `/api/meeting/${meetingData.meeting.number}/agenda-data`, { body: meetingData }).as('getMeetingData')
        cy.visit(`/meeting/${meetingData.meeting.number}/floor-plan-neue`, {
          onBeforeLoad: (win) => { injectMeetingData(win, meetingData.meeting.number) }
        })
        cy.wait('@getMeetingData')
      })

      // -> HEADER

      it(`has IETF ${meetingData.meeting.number} title`, () => {
        cy.get('.floorplan h1').first().contains(`IETF ${meetingData.meeting.number} Floor Plan`)
      })
      it(`has meeting city subtitle`, () => {
        cy.get('.floorplan h4').first().contains(meetingData.meeting.city)
      })
      it(`has meeting date subtitle`, () => {
        cy.get('.floorplan h4').first().contains(/[a-zA-Z] [0-9]{1,2} - ([a-zA-Z]+ )?[0-9]{1,2}, [0-9]{4}/i)
      })

      // -> NAV

      it(`has the correct navigation items`, () => {
        cy.get('.floorplan .meeting-nav > li').should('have.length', 3)
        cy.get('.floorplan .meeting-nav > li').first().contains('Agenda')
        cy.get('.floorplan .meeting-nav > li').eq(1).contains('Floor plan')
        cy.get('.floorplan .meeting-nav > li').last().contains('Plaintext')
      })

      // -> FLOORS

      it(`can switch between floors`, () => {
        cy.get('.floorplan .floorplan-floors > .nav-link').should('have.length', meetingData.floors.length)
        cy.get('.floorplan .floorplan-floors > .nav-link').each((el, idx) => {
          cy.wrap(el).contains(meetingData.floors[idx].name)
          cy.wrap(el).click()
          cy.wrap(el).should('have.class', 'active')
          cy.wrap(el).siblings().should('not.have.class', 'active')
          // Wait for image to load + verify
          cy.get('.floorplan .floorplan-plan > img').should('be.visible').and(img => expect(img[0].naturalWidth).to.be.greaterThan(1))
        })
      })

      // -> ROOMS

      it(`can select rooms`, () => {
        const floor = meetingData.floors[0]
        cy.get('.floorplan .floorplan-floors > .nav-link').first().click()
        cy.get('.floorplan .floorplan-rooms > .list-group-item').should('have.length', floor.rooms.length)
        cy.get('.floorplan .floorplan-rooms > .list-group-item').each((el, idx) => {
          // Room List
          const room = floor.rooms[idx]
          cy.wrap(el).find('strong').contains(room.name)
            .next('small').contains(room.functionalName)
          cy.wrap(el).find('.badge').should('exist').and('include.text', floor.short)
          cy.wrap(el).click()
          cy.wrap(el).should('have.class', 'active')
          cy.wrap(el).siblings().should('not.have.class', 'active')
          // URL query segment
          cy.location('search').should('include', `room=${room.slug}`)
          // Pin Drop
          cy.window().then(win => {
            cy.get('.floorplan .floorplan-plan > img').then(floorImg => {
              const planxRatio = floorImg[0].width / floor.width
              const planyRatio = floorImg[0].height / floor.height
              cy.get('.floorplan .floorplan-plan-pin').should('exist').and('be.visible').then(el => {
                const pinMarginLeft = parseInt(win.getComputedStyle(el[0]).getPropertyValue('margin-left').match(/\d+/))
                const xPos = Math.round((room.left + (room.right - room.left) / 2) * planxRatio) - 25 + pinMarginLeft
                const yPos = Math.round((room.top + (room.bottom - room.top) / 2) * planyRatio) - 40
                expect(el[0].offsetLeft).to.equal(xPos)
                expect(el[0].offsetTop).to.equal(yPos)
              })
            })
          })
        })
      })
    })
  }
})
